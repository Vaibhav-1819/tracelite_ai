"""
Tests for AIClient and Offline Fallback Heuristics
"""

from tracelite.ai_client import AIClient
from tracelite.models import DeterministicAnalysis, StackTrace


def test_ai_fallback_on_zerodivision():
    client = AIClient()
    analysis = DeterministicAnalysis(
        total_lines=15,
        error_count=2,
        warning_count=0,
        stack_traces=[
            StackTrace(
                start_line=7,
                end_line=11,
                language="python",
                exception_type="ZeroDivisionError",
                exception_message="division by zero",
                frames=["  File 'foo.py', line 12"],
                raw_text="ZeroDivisionError: division by zero",
            )
        ],
        error_groups=[],
        timeline=[],
        primary_error="ZeroDivisionError: division by zero",
        masked_secrets_count=0,
    )

    hypothesis = client.investigate(analysis)

    assert hypothesis.is_fallback is True
    assert "Division by Zero" in hypothesis.title
    assert len(hypothesis.likely_causes) >= 2
    assert len(hypothesis.suggested_steps) >= 2
    assert "ZeroDivisionError" in hypothesis.confidence_statement


def test_bounded_evidence_package():
    client = AIClient()
    analysis = DeterministicAnalysis(
        total_lines=5000,
        error_count=120,
        warning_count=30,
        stack_traces=[
            StackTrace(
                start_line=10,
                end_line=25,
                language="python",
                exception_type="ValueError",
                exception_message="invalid literal for int()",
                frames=["line 1", "line 2", "line 3", "line 4", "line 5"],
                raw_text="...",
            )
        ],
        error_groups=[],
        timeline=[],
        primary_error="ValueError: invalid literal",
        masked_secrets_count=2,
    )

    evidence = client.build_evidence_package(analysis)

    assert evidence["total_lines"] == 5000
    assert evidence["error_count"] == 120
    assert len(evidence["stack_traces"]) == 1
    # Frames should be bounded to 4 max
    assert len(evidence["stack_traces"][0]["top_frames"]) <= 4
