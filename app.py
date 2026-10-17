"""
TraceLite AI - Local-First Log & Stack Trace Investigation Assistant
Streamlit Web Application
"""

import os
import uuid
from datetime import datetime
import streamlit as st

from tracelite.parser import LogParser
from tracelite.masker import SecretMasker
from tracelite.ai_client import AIClient
from tracelite.exporter import MarkdownExporter
from tracelite.models import InvestigationReport

# Page configuration
st.set_page_config(
    page_title="TraceLite AI — Local-First Debugging Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Styling (Dark Mode, Glassmorphism, Neon Accents)
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

code, pre {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Header Banner */
.main-header {
    background: linear-gradient(135deg, rgba(24, 24, 37, 0.9) 0%, rgba(30, 27, 75, 0.9) 100%);
    border: 1px solid rgba(139, 92, 246, 0.25);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    backdrop-filter: blur(10px);
}

.main-title {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

.main-subtitle {
    color: #94a3b8;
    font-size: 1.05rem;
    margin-top: 6px;
    font-weight: 400;
}

/* Metric Glass Cards */
.metric-card {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    border-color: rgba(99, 102, 241, 0.4);
}

.metric-val {
    font-size: 1.8rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 4px 0;
}

.metric-label {
    font-size: 0.85rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}

/* Alert Boxes */
.glass-alert {
    background: rgba(15, 23, 42, 0.75);
    border-left: 4px solid #6366f1;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 16px 0;
}

.glass-alert-warn {
    border-left-color: #f59e0b;
    background: rgba(245, 158, 11, 0.08);
}

.glass-alert-danger {
    border-left-color: #ef4444;
    background: rgba(239, 68, 68, 0.08);
}

.glass-alert-success {
    border-left-color: #10b981;
    background: rgba(16, 185, 129, 0.08);
}

.badge-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-right: 8px;
}

.badge-ai {
    background: rgba(99, 102, 241, 0.2);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.4);
}

.badge-fallback {
    background: rgba(245, 158, 11, 0.2);
    color: #fcd34d;
    border: 1px solid rgba(245, 158, 11, 0.4);
}

.badge-privacy {
    background: rgba(16, 185, 129, 0.2);
    color: #6ee7b7;
    border: 1px solid rgba(16, 185, 129, 0.4);
}

/* Trace Box */
.trace-container {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 16px;
    overflow-x: auto;
    font-size: 0.88rem;
    line-height: 1.5;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Initialize Session State
if "raw_logs" not in st.session_state:
    st.session_state.raw_logs = ""
if "active_report" not in st.session_state:
    st.session_state.active_report = None


# Helper to load sample fixtures
def load_fixture(filename: str):
    base_dir = os.path.dirname(__file__)
    fixture_path = os.path.join(base_dir, "fixtures", filename)
    if os.path.exists(fixture_path):
        with open(fixture_path, "r", encoding="utf-8") as f:
            st.session_state.raw_logs = f.read()
    else:
        st.error(f"Sample fixture {filename} not found.")


# --- SIDEBAR: Configuration & Sample Fixtures ---
with st.sidebar:
    st.markdown("### ⚙️ Engine Settings")

    ollama_host = st.text_input(
        "Ollama Endpoint",
        value="http://localhost:11434",
        help="Local Ollama URL. Default is http://localhost:11434",
    )

    model_name = st.text_input(
        "Model Name",
        value="qwen2.5:0.5b",
        help="Open-weight model (e.g., qwen2.5:0.5b, llama3.2:1b, qwen2.5-coder:0.5b)",
    )

    ai_client = AIClient(base_url=ollama_host, model_name=model_name)
    is_online, status_msg, models_avail = ai_client.check_ollama_available()

    if is_online:
        st.markdown(
            f'<div class="glass-alert glass-alert-success"><span class="badge-pill badge-privacy">● Online</span><br><small>{status_msg}</small></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="glass-alert glass-alert-warn"><span class="badge-pill badge-fallback">● Offline Fallback</span><br><small>Ollama not detected at endpoint. Heuristic rule engine active.</small></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### 📂 Quick-Load Sample Fixtures")
    st.caption("Load curated logs to verify the end-to-end investigation workflow:")

    if st.button("🐍 Python ZeroDivisionError", use_container_width=True):
        load_fixture("python_zero_division.log")
        st.rerun()

    if st.button("☕ Java NullPointerException", use_container_width=True):
        load_fixture("java_null_pointer.log")
        st.rerun()

    if st.button("🌐 HTTP 500 & 429 Rate Limits", use_container_width=True):
        load_fixture("http_server_errors.log")
        st.rerun()

    st.markdown("---")
    st.markdown("### 🛡️ Privacy Guarantee")
    st.caption(
        "TraceLite AI processes all logs strictly on your local machine. "
        "Credentials, tokens, and database passwords are automatically redacted. "
        "Zero data is sent to third-party cloud services."
    )


# --- MAIN HEADER ---
st.markdown(
    """
    <div class="main-header">
        <h1 class="main-title">TraceLite AI</h1>
        <div class="main-subtitle">
            Local-first log triage & stack trace investigation assistant powered by open-weight AI.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# --- INPUT SECTION: File Upload or Paste ---
input_col1, input_col2 = st.columns([3, 1])

with input_col1:
    uploaded_file = st.file_uploader(
        "Upload a log file (.log, .txt) — Max 10MB",
        type=["log", "txt"],
        help="Upload standard application logs, system journal, or crash dumps.",
    )
    if uploaded_file is not None:
        try:
            st.session_state.raw_logs = uploaded_file.read().decode("utf-8", errors="replace")
        except Exception as e:
            st.error(f"Error reading uploaded file: {e}")

with input_col2:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if st.button("🗑️ Clear Input", use_container_width=True):
        st.session_state.raw_logs = ""
        st.session_state.active_report = None
        st.rerun()


raw_input = st.text_area(
    "Or paste raw log text / stack trace below:",
    value=st.session_state.raw_logs,
    height=200,
    placeholder="Paste traceback, Docker container logs, Nginx access logs, or JVM crash output here...",
)

# Keep session state in sync
st.session_state.raw_logs = raw_input


# --- ACTION BUTTON ---
action_col1, action_col2 = st.columns([1, 4])
with action_col1:
    analyze_btn = st.button("🔍 Investigate Logs", type="primary", use_container_width=True)

with action_col2:
    if raw_input.strip():
        line_count = len(raw_input.splitlines())
        st.caption(f"📊 Input status: **{line_count:,} lines** ({len(raw_input):,} characters) ready for analysis.")


# --- RUN INVESTIGATION ---
if analyze_btn:
    if not raw_input.strip():
        st.warning("Please paste log text or upload a log file first.")
    else:
        with st.spinner("Parsing logs, masking secrets, and extracting evidence..."):
            parser = LogParser()
            analysis = parser.parse(raw_input)

            # AI Investigation (Ollama or Graceful Heuristic Fallback)
            hypothesis = ai_client.investigate(analysis)

            # Create report object
            report = InvestigationReport(
                report_id=f"TL-{uuid.uuid4().hex[:8].upper()}",
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                analysis=analysis,
                hypothesis=hypothesis,
                raw_log_sample=raw_input[:10000],
            )
            st.session_state.active_report = report


# --- REPORT DISPLAY ---
report: InvestigationReport = st.session_state.active_report

if report:
    analysis = report.analysis
    hyp = report.hypothesis

    st.markdown("---")

    # Metrics Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Lines Analyzed</div>
                <div class="metric-val">{analysis.total_lines:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Errors Detected</div>
                <div class="metric-val" style="color: #f87171;">{analysis.error_count:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Warnings</div>
                <div class="metric-val" style="color: #fbbf24;">{analysis.warning_count:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Stack Traces</div>
                <div class="metric-val" style="color: #a78bfa;">{len(analysis.stack_traces)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m5:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Secrets Masked</div>
                <div class="metric-val" style="color: #34d399;">{analysis.masked_secrets_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Primary Error Banner
    if analysis.primary_error:
        st.error(f"🚨 **Primary Isolated Error:** `{analysis.primary_error}`")

    # Tabs for structured navigation
    tab_report, tab_evidence, tab_clusters, tab_timeline, tab_export = st.tabs([
        "🧠 AI Investigation",
        "📑 Extracted Traces & Evidence",
        "📊 Frequency & Patterns",
        "⏱️ Timeline Analysis",
        "📥 Export Report",
    ])

    # TAB 1: AI Investigation
    with tab_report:
        col_ai, col_meta = st.columns([3, 1])

        with col_ai:
            st.markdown(f"### {hyp.title}")

            badge_html = (
                f'<span class="badge-pill badge-fallback">Heuristic Rule Mode</span>'
                if hyp.is_fallback
                else f'<span class="badge-pill badge-ai">Local LLM: {hyp.model_name}</span>'
            )
            st.markdown(f"{badge_html}", unsafe_allow_html=True)

            st.markdown(f"**Explanation:**\n\n{hyp.explanation}")

            st.markdown("#### 🎯 Plausible Root Causes")
            for idx, cause in enumerate(hyp.likely_causes, 1):
                st.markdown(f"- **Hypothesis {idx}:** {cause}")

            st.markdown("#### 🛠️ Recommended Diagnostic Steps")
            for idx, step in enumerate(hyp.suggested_steps, 1):
                st.checkbox(f"{step}", key=f"step_{idx}", value=False)

        with col_meta:
            st.markdown("#### 🔬 AI Transparency")
            st.info(
                f"**Confidence Assessment:**\n\n{hyp.confidence_statement}\n\n"
                "*Notice: AI hypotheses are generated from bounded log excerpts. "
                "TraceLite has not executed code or verified an automated patch.*"
            )
            if hyp.evidence_referenced:
                st.markdown("**Evidence Anchors:**")
                for ev in hyp.evidence_referenced:
                    st.caption(f"• `{ev[:60]}`")

    # TAB 2: Stack Traces & Evidence
    with tab_evidence:
        st.markdown("### 🧩 Structured Stack Traces")
        if analysis.stack_traces:
            for idx, st_obj in enumerate(analysis.stack_traces, 1):
                with st.expander(
                    f"Trace #{idx}: {st_obj.exception_type} ({st_obj.language.upper()}) — Lines {st_obj.start_line} to {st_obj.end_line}",
                    expanded=(idx == 1),
                ):
                    st.markdown(f"**Exception Message:** `{st_obj.exception_message}`")
                    st.code(st_obj.raw_text, language=st_obj.language)
        else:
            st.info("No standard multi-line stack traces (Python, Java, Node, Go) detected in the provided input.")

        st.markdown("### 🔍 Side-by-Side Context Verification")
        st.caption("Compare extracted exception with surrounding log lines to verify AI reasoning.")
        st.text_area("Surrounding Context Excerpt:", value=report.raw_log_sample[:3000], height=180, disabled=True)

    # TAB 3: Frequency & Error Clusters
    with tab_clusters:
        st.markdown("### 🔁 Recurring Error Signatures")
        st.caption("TraceLite normalizes dynamic variables (IPs, numbers, timestamps) to cluster repeated messages.")

        if analysis.error_groups:
            cluster_data = []
            for g in analysis.error_groups:
                cluster_data.append({
                    "Occurrences": g.count,
                    "First Line": f"L{g.first_seen_line}",
                    "Last Line": f"L{g.last_seen_line}",
                    "Normalized Signature": g.signature,
                    "Sample Message": g.sample_message,
                })
            st.dataframe(cluster_data, use_container_width=True)
        else:
            st.info("No repeated error clusters identified.")

    # TAB 4: Timeline Analysis
    with tab_timeline:
        st.markdown("### ⏱️ Error & Event Timeline")
        if analysis.timeline:
            timeline_data = []
            for tp in analysis.timeline:
                timeline_data.append({
                    "Time Bucket": tp.timestamp,
                    "Errors": tp.error_count,
                    "Warnings": tp.warning_count,
                    "Info": tp.info_count,
                })
            st.bar_chart(
                data=timeline_data,
                x="Time Bucket",
                y=["Errors", "Warnings"],
                color=["#ef4444", "#f59e0b"],
            )
            st.table(timeline_data)
        else:
            st.info("No standard timestamps detected in log lines to construct a chronological timeline.")

    # TAB 5: Export Report
    with tab_export:
        st.markdown("### 📥 Export & Share Investigation")
        st.caption("Generate a clean Markdown document ready for GitHub Issues, Pull Requests, or team Slack/Discord.")

        markdown_report = MarkdownExporter.export(report)

        exp_col1, exp_col2 = st.columns([1, 1])
        with exp_col1:
            st.download_button(
                label="⬇️ Download Markdown Report (.md)",
                data=markdown_report,
                file_name=f"tracelite_report_{report.report_id}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with exp_col2:
            st.button("📋 Copy to Clipboard (Show Preview)", use_container_width=True)

        st.markdown("#### Markdown Preview:")
        st.code(markdown_report, language="markdown")
