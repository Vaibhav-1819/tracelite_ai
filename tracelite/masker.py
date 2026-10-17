"""
TraceLite AI - Secret & Sensitive Data Masker
Redacts API keys, credentials, tokens, and connection strings before display or AI processing.
"""

import re
from typing import Tuple, List

# Common patterns for credentials and secrets
SECRET_PATTERNS = [
    # AWS Access Key ID
    (re.compile(r'\b(AKIA[0-9A-Z]{16})\b'), '[REDACTED_AWS_KEY]'),
    # Generic API Keys / Tokens (hex or base64 length >= 24)
    (re.compile(r'(?i)\b(api[_-]?key|access[_-]?token|auth[_-]?token|secret[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{16,})["\']?'), r'\1=[REDACTED_TOKEN]'),
    # OpenAI API Key format
    (re.compile(r'\bsk-[a-zA-Z0-9_-]{20,}\b'), '[REDACTED_OPENAI_KEY]'),
    # GitHub Tokens
    (re.compile(r'\b(gh[pousr]_[A-Za-z0-9_]{36,})\b'), '[REDACTED_GITHUB_TOKEN]'),
    # Bearer Tokens
    (re.compile(r'(?i)\bBearer\s+([a-zA-Z0-9_\-\.]{15,})\b'), 'Bearer [REDACTED_BEARER_TOKEN]'),
    # Passwords in URLs / queries / configs
    (re.compile(r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^"\'\s,;]+)["\']?'), r'\1="[REDACTED_PASSWORD]"'),
    # Database URIs with credentials
    (re.compile(r'(?i)(postgres|postgresql|mysql|mongodb|redis)://([^:@\s]+):([^@\s]+)@'), r'\1://\2:[REDACTED_PWD]@'),
    # JWT Tokens (3 segments separated by dot)
    (re.compile(r'\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b'), '[REDACTED_JWT_TOKEN]'),
    # Private Keys
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----'), '[REDACTED_PRIVATE_KEY]'),
]


class SecretMasker:
    """Masks secrets and sensitive credentials from log text."""

    def __init__(self):
        self.patterns = SECRET_PATTERNS

    def mask_text(self, text: str) -> Tuple[str, int]:
        """
        Masks all recognized secrets in the given text.
        Returns:
            Tuple[str, int]: Sanitized text and total number of redactions made.
        """
        sanitized = text
        total_redactions = 0

        for pattern, replacement in self.patterns:
            matches = list(pattern.finditer(sanitized))
            if matches:
                total_redactions += len(matches)
                sanitized = pattern.sub(replacement, sanitized)

        return sanitized, total_redactions

    def mask_lines(self, lines: List[str]) -> Tuple[List[str], int]:
        """Masks secrets line by line."""
        masked_lines = []
        total_redactions = 0
        for line in lines:
            clean, count = self.mask_text(line)
            masked_lines.append(clean)
            total_redactions += count
        return masked_lines, total_redactions
