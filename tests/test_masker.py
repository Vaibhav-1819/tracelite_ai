"""
Tests for SecretMasker
"""

import pytest
from tracelite.masker import SecretMasker


def test_mask_openai_key():
    masker = SecretMasker()
    raw = "Failed call with key sk-abcdef1234567890abcdef1234567890 in config"
    clean, count = masker.mask_text(raw)
    assert "[REDACTED_OPENAI_KEY]" in clean
    assert "sk-abcdef" not in clean
    assert count == 1


def test_mask_aws_key():
    masker = SecretMasker()
    raw = "AWS access key AKIAIOSFODNN7EXAMPLE used for S3 bucket upload"
    clean, count = masker.mask_text(raw)
    assert "[REDACTED_AWS_KEY]" in clean
    assert "AKIAIOSFODNN7EXAMPLE" not in clean
    assert count == 1


def test_mask_bearer_token():
    masker = SecretMasker()
    raw = "Headers: {'Authorization': 'Bearer a1b2c3d4e5f6g7h8i9j0k1l2m3'}"
    clean, count = masker.mask_text(raw)
    assert "Bearer [REDACTED_BEARER_TOKEN]" in clean
    assert count == 1


def test_mask_password_and_db_uri():
    masker = SecretMasker()
    raw = "Connecting to postgres://admin:SuperSecretPass123@db.internal:5432/production"
    clean, count = masker.mask_text(raw)
    assert "SuperSecretPass123" not in clean
    assert "[REDACTED_PWD]" in clean
    assert count >= 1
