"""
TraceLite AI - Markdown Report Exporter
Generates structured GitHub-flavored Markdown investigation reports
with clear separation of factual evidence vs AI hypotheses.
"""

from datetime import datetime
from typing import Optional
from .models import InvestigationReport, DeterministicAnalysis, AIHypothesis


class MarkdownExporter:
    """Formats investigation reports into standard Markdown documents."""

    @staticmethod
    def export(report: InvestigationReport, include_raw_sample: bool = True) -> str:
        """Renders an evidence-first Markdown investigation report."""
        analysis = report.analysis
        hyp = report.hypothesis

        engine_badge = (
            f"`Offline Heuristic Rules`"
            if hyp.is_fallback
            else f"`Local Open-Weight Model: {hyp.model_name}`"
        )

        md_lines = [
            "# 🔍 TraceLite AI — Investigation Report",
            "",
            f"**Report ID:** `{report.report_id}`  ",
            f"**Generated At:** `{report.generated_at}`  ",
            f"**Inference Engine:** {engine_badge}  ",
            f"**Secrets Masked:** `{analysis.masked_secrets_count}` detected & redacted  ",
            "",
            "---",
            "",
            "## 1. Executive Summary",
            "",
            f"- **Primary Error:** `{analysis.primary_error or 'None Detected'}`",
            f"- **Total Lines Analyzed:** {analysis.total_lines:,}",
            f"- **Total Error Events:** {analysis.error_count:,}",
            f"- **Total Warnings:** {analysis.warning_count:,}",
            f"- **Stack Traces Isolated:** {len(analysis.stack_traces)}",
            f"- **Unique Recurring Error Signatures:** {len(analysis.error_groups)}",
            "",
            "---",
            "",
            "## 2. AI Investigation & Hypotheses",
            "",
            f"### {hyp.title}",
            "",
            f"> [!IMPORTANT]",
            f"> **Confidence / Transparency Statement:**  ",
            f"> {hyp.confidence_statement}",
            f"> *Disclaimer: AI explanations are hypotheses derived from bounded evidence. TraceLite has not executed code or verified a fix.*",
            "",
            "#### Explanation",
            hyp.explanation,
            "",
            "#### Plausible Root Causes",
        ]

        for idx, cause in enumerate(hyp.likely_causes, 1):
            md_lines.append(f"{idx}. {cause}")

        md_lines.append("")
        md_lines.append("#### Recommended Diagnostic Steps")
        for idx, step in enumerate(hyp.suggested_steps, 1):
            md_lines.append(f"{idx}. [ ] {step}")

        md_lines.extend([
            "",
            "---",
            "",
            "## 3. Extracted Evidence (Deterministic Facts)",
            "",
        ])

        # Stack Traces
        if analysis.stack_traces:
            md_lines.append("### Primary Stack Traces")
            for idx, st in enumerate(analysis.stack_traces, 1):
                md_lines.extend([
                    f"#### Trace #{idx}: `{st.exception_type}` ({st.language.capitalize()})",
                    f"- **Lines in Log:** {st.start_line} – {st.end_line}",
                    f"- **Message:** `{st.exception_message}`",
                    "",
                    f"```{st.language if st.language != 'generic' else 'text'}",
                    st.raw_text,
                    "```",
                    "",
                ])
        else:
            md_lines.extend([
                "> *No structured multi-line stack traces were detected.*",
                "",
            ])

        # Recurring Error Groups
        if analysis.error_groups:
            md_lines.extend([
                "### Recurring Error Patterns",
                "",
                "| Count | First Line | Last Line | Sample Message |",
                "|:-----:|:----------:|:---------:|:---------------|",
            ])
            for eg in analysis.error_groups[:10]:
                clean_sample = eg.sample_message.replace("|", "\\|")
                md_lines.append(
                    f"| **{eg.count}** | L{eg.first_seen_line} | L{eg.last_seen_line} | `{clean_sample[:90]}` |"
                )
            md_lines.append("")

        # Timeline
        if analysis.timeline:
            md_lines.extend([
                "### Error Distribution Timeline",
                "",
                "| Time Bucket | Errors | Warnings | Info/Other |",
                "|:------------|:------:|:--------:|:----------:|",
            ])
            for tp in analysis.timeline[:15]:
                md_lines.append(f"| `{tp.timestamp}` | {tp.error_count} | {tp.warning_count} | {tp.info_count} |")
            md_lines.append("")

        # Raw sample appendix
        if include_raw_sample and report.raw_log_sample:
            md_lines.extend([
                "---",
                "",
                "## 4. Context Log Excerpt",
                "",
                "<details>",
                "<summary>Click to expand sanitized raw log context</summary>",
                "",
                "```text",
                report.raw_log_sample[:5000],
                "```",
                "</details>",
                "",
            ])

        md_lines.extend([
            "---",
            "*Report generated with [TraceLite AI](https://github.com/vaibhav/tracelite-ai) — Local-first, open-source debugging assistant.*",
        ])

        return "\n".join(md_lines)
