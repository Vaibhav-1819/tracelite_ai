"""
Tests for MarkdownExporter
"""

from tracelite.exporter import MarkdownExporter
from tracelite.models import (
    InvestigationReport,
    DeterministicAnalysis,
    AIHypothesis,
    StackTrace,
    ErrorGroup,
)


def test_markdown_report_export():
    report = InvestigationReport(
        report_id="TL-TEST-001",
        generated_at="2026-10-18 10:30:00",
        analysis=DeterministicAnalysis(
            total_lines=100,
            error_count=5,
            warning_count=2,
            stack_traces=[
                StackTrace(
                    start_line=12,
                    end_line=16,
                    language="python",
                    exception_type="ZeroDivisionError",
                    exception_message="division by zero",
                    frames=["File billing.py, line 87"],
                    raw_text="ZeroDivisionError: division by zero",
                )
            ],
            error_groups=[
                ErrorGroup(
                    signature="POST /api/checkout <NUM>",
                    sample_message="POST /api/checkout 500",
                    count=4,
                    first_seen_line=10,
                    last_seen_line=14,
                )
            ],
            timeline=[],
            primary_error="ZeroDivisionError: division by zero",
            masked_secrets_count=1,
        ),
        hypothesis=AIHypothesis(
            title="Division by Zero Detected",
            explanation="Denominator evaluated to 0 during discount calculation.",
            likely_causes=["Empty item list", "Missing default value"],
            suggested_steps=["Add guard check", "Verify batch input data"],
            confidence_statement="High confidence based on traceback",
            model_name="deterministic-heuristics",
            is_fallback=True,
        ),
        raw_log_sample="2026-10-18 10:14:04 [ERROR] ZeroDivisionError: division by zero",
    )

    markdown = MarkdownExporter.export(report)

    assert "# 🔍 TraceLite AI — Investigation Report" in markdown
    assert "TL-TEST-001" in markdown
    assert "ZeroDivisionError: division by zero" in markdown
    assert "Division by Zero Detected" in markdown
    assert "Add guard check" in markdown
    assert "POST /api/checkout 500" in markdown
    assert "TraceLite has not executed code or verified a fix" in markdown
