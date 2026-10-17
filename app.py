"""
TraceLite AI - Local-First Log & Stack Trace Investigation Assistant
Streamlit Web Application with Multi-Page Navigation, Space Grotesk Typography, and Modern Footer
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
    initial_sidebar_state="collapsed",
)

# Modern Grotesk Typography & Glassmorphism Design System
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: #0b0f19;
    color: #f1f5f9;
}

h1, h2, h3, h4, h5, h6, .main-title, .metric-val {
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.02em;
}

code, pre, .trace-container {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Floating Glassmorphic Top Navbar */
.top-navbar {
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 16px;
    padding: 12px 24px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
}

.brand-wrapper {
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-logo {
    font-size: 1.45rem;
    font-weight: 700;
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.brand-pill {
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #a5b4fc;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 9999px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Metric Glass Cards */
.metric-card {
    background: rgba(30, 41, 59, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 18px 20px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    border-color: rgba(129, 140, 248, 0.4);
}

.metric-val {
    font-size: 1.9rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 4px 0;
}

.metric-label {
    font-size: 0.8rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
}

/* Feature & Architecture Cards */
.info-card {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.2);
}

.info-card h3 {
    margin-top: 0;
    color: #38bdf8;
    font-size: 1.3rem;
}

/* Badge Pills */
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

/* Footer Styling */
.app-footer {
    margin-top: 60px;
    padding: 32px 24px;
    border-top: 1px solid rgba(148, 163, 184, 0.12);
    background: rgba(11, 15, 25, 0.9);
    border-radius: 16px 16px 0 0;
    text-align: center;
}

.footer-links {
    display: flex;
    justify-content: center;
    gap: 24px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}

.footer-links a {
    color: #94a3b8;
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 500;
    transition: color 0.2s ease;
}

.footer-links a:hover {
    color: #38bdf8;
}

.footer-text {
    color: #64748b;
    font-size: 0.85rem;
    margin: 4px 0;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Session State Initialization
if "raw_logs" not in st.session_state:
    st.session_state.raw_logs = ""
if "active_report" not in st.session_state:
    st.session_state.active_report = None
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "🔍 Log Investigator"


def load_fixture(filename: str):
    base_dir = os.path.dirname(__file__)
    fixture_path = os.path.join(base_dir, "fixtures", filename)
    if os.path.exists(fixture_path):
        with open(fixture_path, "r", encoding="utf-8") as f:
            st.session_state.raw_logs = f.read()


# --- TOP NAVBAR ---
nav_col_logo, nav_col_links, nav_col_github = st.columns([1.8, 4.2, 1.2])

with nav_col_logo:
    st.markdown(
        """
        <div class="brand-wrapper" style="padding-top: 6px;">
            <span class="brand-logo">TraceLite AI</span>
            <span class="brand-pill">v1.0 Local</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with nav_col_links:
    pages = [
        "🔍 Log Investigator",
        "🚀 Architecture",
        "📖 Docs & CLI",
        "💼 Side Hustle & Pricing",
        "🛡️ Privacy Engine",
    ]
    selected_page = st.radio(
        "Navigation",
        options=pages,
        index=pages.index(st.session_state.nav_page),
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.nav_page = selected_page

with nav_col_github:
    st.markdown(
        """
        <div style="text-align: right; padding-top: 4px;">
            <a href="https://github.com/Vaibhav-1819/tracelite_ai" target="_blank" style="text-decoration: none;">
                <button style="background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(255,255,255,0.15); color: #f8fafc; padding: 6px 14px; border-radius: 8px; font-weight: 600; font-size: 0.85rem; cursor: pointer;">
                    ⭐ GitHub
                </button>
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<hr style='border: none; border-bottom: 1px solid rgba(148, 163, 184, 0.12); margin: 12px 0 24px 0;'>", unsafe_allow_html=True)


# --- PAGE 1: LOG INVESTIGATOR ---
if st.session_state.nav_page == "🔍 Log Investigator":

    # Sidebar with Model & Quick-Load Fixtures
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
            help="Open-weight model (e.g. qwen2.5:0.5b, llama3.2:1b)",
        )

        ai_client = AIClient(base_url=ollama_host, model_name=model_name)
        is_online, status_msg, _ = ai_client.check_ollama_available()

        if is_online:
            st.success(f"● Online ({status_msg})")
        else:
            st.warning("● Offline Mode (Heuristic rules active)")

        st.markdown("---")
        st.markdown("### 📂 Quick Sample Fixtures")
        if st.button("🐍 Python ZeroDivisionError", use_container_width=True):
            load_fixture("python_zero_division.log")
            st.rerun()

        if st.button("☕ Java NullPointerException", use_container_width=True):
            load_fixture("java_null_pointer.log")
            st.rerun()

        if st.button("🌐 HTTP 500 & 429 Rate Limits", use_container_width=True):
            load_fixture("http_server_errors.log")
            st.rerun()

    # Hero Banner
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, rgba(30, 27, 75, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(129, 140, 248, 0.2); border-radius: 16px; padding: 24px 30px; margin-bottom: 24px;">
            <h1 style="margin: 0; font-size: 2.2rem; background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Investigate Application Logs
            </h1>
            <p style="color: #94a3b8; font-size: 1.05rem; margin: 6px 0 0 0;">
                Deterministic stack trace extraction paired with local open-weight AI. No cloud APIs, zero per-token fees.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Input Section
    input_col1, input_col2 = st.columns([3, 1])

    with input_col1:
        uploaded_file = st.file_uploader(
            "Upload log file (.log, .txt)",
            type=["log", "txt"],
            help="Upload raw logs or crash traces",
        )
        if uploaded_file is not None:
            try:
                st.session_state.raw_logs = uploaded_file.read().decode("utf-8", errors="replace")
            except Exception as e:
                st.error(f"Error reading file: {e}")

    with input_col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Log Area", use_container_width=True):
            st.session_state.raw_logs = ""
            st.session_state.active_report = None
            st.rerun()

    raw_input = st.text_area(
        "Or paste stack trace / terminal crash output:",
        value=st.session_state.raw_logs,
        height=190,
        placeholder="Paste Python traceback, Java JVM error, Docker container logs, or Nginx access logs...",
    )
    st.session_state.raw_logs = raw_input

    # Action Controls
    action_col1, action_col2 = st.columns([1.2, 4])
    with action_col1:
        analyze_btn = st.button("🔍 Investigate Logs", type="primary", use_container_width=True)

    with action_col2:
        if raw_input.strip():
            line_count = len(raw_input.splitlines())
            st.caption(f"📊 Ready: **{line_count:,} lines** ({len(raw_input):,} characters) prepared for analysis.")

    # Execution
    if analyze_btn:
        if not raw_input.strip():
            st.warning("Please paste log text or select a sample fixture first.")
        else:
            with st.spinner("Analyzing log structure, redacting secrets, and building report..."):
                parser = LogParser()
                analysis = parser.parse(raw_input)
                ai_client = AIClient()
                hypothesis = ai_client.investigate(analysis)

                report = InvestigationReport(
                    report_id=f"TL-{uuid.uuid4().hex[:8].upper()}",
                    generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    analysis=analysis,
                    hypothesis=hypothesis,
                    raw_log_sample=raw_input[:10000],
                )
                st.session_state.active_report = report

    # Results Display
    report: InvestigationReport = st.session_state.active_report
    if report:
        analysis = report.analysis
        hyp = report.hypothesis

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Metrics Row
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Lines Analyzed</div><div class="metric-val">{analysis.total_lines:,}</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Errors Detected</div><div class="metric-val" style="color: #f87171;">{analysis.error_count:,}</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Warnings</div><div class="metric-val" style="color: #fbbf24;">{analysis.warning_count:,}</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Stack Traces</div><div class="metric-val" style="color: #a78bfa;">{len(analysis.stack_traces)}</div></div>', unsafe_allow_html=True)
        with m5:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Secrets Masked</div><div class="metric-val" style="color: #34d399;">{analysis.masked_secrets_count}</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        if analysis.primary_error:
            st.error(f"🚨 **Primary Isolated Error:** `{analysis.primary_error}`")

        tab_report, tab_evidence, tab_clusters, tab_timeline, tab_export = st.tabs([
            "🧠 AI Investigation",
            "📑 Extracted Traces & Evidence",
            "📊 Frequency & Patterns",
            "⏱️ Timeline Analysis",
            "📥 Export Report",
        ])

        with tab_report:
            col_ai, col_meta = st.columns([3, 1])
            with col_ai:
                st.markdown(f"### {hyp.title}")
                badge_html = '<span class="badge-pill badge-fallback">Heuristic Rule Mode</span>' if hyp.is_fallback else f'<span class="badge-pill badge-ai">Local LLM: {hyp.model_name}</span>'
                st.markdown(badge_html, unsafe_allow_html=True)
                st.markdown(f"**Explanation:**\n\n{hyp.explanation}")
                st.markdown("#### 🎯 Plausible Root Causes")
                for idx, cause in enumerate(hyp.likely_causes, 1):
                    st.markdown(f"- **Hypothesis {idx}:** {cause}")
                st.markdown("#### 🛠️ Recommended Diagnostic Checklist")
                for idx, step in enumerate(hyp.suggested_steps, 1):
                    st.checkbox(f"{step}", key=f"step_{idx}", value=False)

            with col_meta:
                st.markdown("#### 🔬 AI Transparency")
                st.info(f"**Confidence:**\n\n{hyp.confidence_statement}\n\n*Notice: Hypotheses are generated from bounded evidence. TraceLite never modifies code automatically.*")

        with tab_evidence:
            st.markdown("### 🧩 Structured Stack Traces")
            if analysis.stack_traces:
                for idx, st_obj in enumerate(analysis.stack_traces, 1):
                    with st.expander(f"Trace #{idx}: {st_obj.exception_type} ({st_obj.language.upper()}) — Lines {st_obj.start_line} to {st_obj.end_line}", expanded=(idx == 1)):
                        st.markdown(f"**Exception Message:** `{st_obj.exception_message}`")
                        st.code(st_obj.raw_text, language=st_obj.language)
            else:
                st.info("No standard multi-line stack traces detected.")

        with tab_clusters:
            st.markdown("### 🔁 Recurring Error Signatures")
            if analysis.error_groups:
                cluster_data = [{"Occurrences": g.count, "First Line": f"L{g.first_seen_line}", "Last Line": f"L{g.last_seen_line}", "Normalized Signature": g.signature, "Sample Message": g.sample_message} for g in analysis.error_groups]
                st.dataframe(cluster_data, use_container_width=True)
            else:
                st.info("No repeated error clusters identified.")

        with tab_timeline:
            st.markdown("### ⏱️ Error & Event Timeline")
            if analysis.timeline:
                timeline_data = [{"Time Bucket": tp.timestamp, "Errors": tp.error_count, "Warnings": tp.warning_count, "Info": tp.info_count} for tp in analysis.timeline]
                st.bar_chart(data=timeline_data, x="Time Bucket", y=["Errors", "Warnings"], color=["#ef4444", "#f59e0b"])
            else:
                st.info("No standard timestamps found to build timeline.")

        with tab_export:
            st.markdown("### 📥 Export Markdown Investigation Report")
            markdown_report = MarkdownExporter.export(report)
            exp_col1, exp_col2 = st.columns([1, 1])
            with exp_col1:
                st.download_button(label="⬇️ Download Markdown Report (.md)", data=markdown_report, file_name=f"tracelite_report_{report.report_id}.md", mime="text/markdown", use_container_width=True)
            with exp_col2:
                st.button("📋 Clipboard Copy Ready (Below)", use_container_width=True)
            st.code(markdown_report, language="markdown")


# --- PAGE 2: ARCHITECTURE & ENGINE ---
elif st.session_state.nav_page == "🚀 Architecture":
    st.markdown("## 🚀 Engine Architecture & The Bounded Evidence Pipeline")
    st.markdown("TraceLite AI pairs deterministic parsing with small open-weight language models to keep debugging fast, cheap, and private.")

    col_arch1, col_arch2 = st.columns([1.5, 1])

    with col_arch1:
        st.markdown(
            """
            <div class="info-card">
                <h3>1. Ingestion & Secret Redaction</h3>
                <p>Raw logs first pass through <code>SecretMasker</code>. Regex patterns identify and redact OpenAI tokens (<code>sk-...</code>), AWS access keys, GitHub personal tokens, Bearer authorization headers, and database connection strings before content is stored or processed.</p>
            </div>
            <div class="info-card">
                <h3>2. Deterministic Parsing Engine</h3>
                <p>Rather than asking an LLM to read 5,000 raw lines, a deterministic Python engine extracts multi-language stack traces (Python, Java JVM, Node.js, Go), normalizes dynamic tokens (UUIDs, IP addresses, memory addresses), and groups repeated error messages.</p>
            </div>
            <div class="info-card">
                <h3>3. Bounded Evidence Packaging</h3>
                <p>The parser packages only the essential evidence: the primary isolated exception, top stack trace frames, top 3 recurring error signatures, and the timeline distribution. This bounded payload fits under 350 tokens, ideal for 0.5B parameter models.</p>
            </div>
            <div class="info-card">
                <h3>4. Ollama Runtime with Offline Heuristic Fallback</h3>
                <p>Inference runs on <code>Qwen2.5-0.5B-Instruct</code> locally via Ollama. If Ollama is offline or uninstalled, TraceLite automatically falls back to built-in deterministic heuristic diagnosis without failing.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_arch2:
        st.markdown("### 🔬 Architectural Flow")
        st.code(
            """
[Raw Logs & Traces]
        │
        ▼
[SecretMasker Engine]
        │ (Redacts tokens/passwords)
        ▼
[Deterministic Parser]
  • Python / Java / Node / Go
  • Duplicate message clustering
  • Timestamp timeline
        │
        ▼
[Bounded Evidence Package]
   (<350 token JSON payload)
   ├── Ollama Online: Qwen2.5-0.5B
   └── Ollama Offline: Heuristics
        │
        ▼
[Evidence-First Report]
  • Isolated primary error
  • Plausible root causes
  • Ordered diagnostic steps
  • Markdown report export
            """,
            language="text",
        )


# --- PAGE 3: DOCUMENTATION & CLI ---
elif st.session_state.nav_page == "📖 Docs & CLI":
    st.markdown("## 📖 Documentation & Setup Guide")

    st.markdown(
        """
        ### 🛠️ Quick Installation
        ```bash
        # 1. Clone the repository
        git clone https://github.com/Vaibhav-1819/tracelite_ai.git
        cd tracelite_ai

        # 2. Install dependencies
        pip install -r requirements.txt

        # 3. (Optional) Run local model with Ollama
        ollama run qwen2.5:0.5b

        # 4. Launch Streamlit UI
        streamlit run app.py
        ```

        ---
        ### 🧪 Running the Broken Billing Demo App
        We bundled a deliberately broken billing service in `demo_app.py` that triggers an unhandled `ZeroDivisionError` alongside a simulated sensitive token:
        ```bash
        python demo_app.py
        ```
        In the UI, click **🐍 Python ZeroDivisionError** in the sidebar to test the full pipeline.

        ---
        ### 🧪 Running the Automated Test Suite
        TraceLite includes 11 automated pytest tests covering the parser, secret redactor, bounded evidence package, and report exporter:
        ```bash
        pytest -v
        ```
        """
    )


# --- PAGE 4: SIDE HUSTLE & PRICING ---
elif st.session_state.nav_page == "💼 Side Hustle & Pricing":
    st.markdown("## 💼 The Side Hustle Thesis & Commercial Model")
    st.markdown("TraceLite AI is built on a sustainable open-core business model tailored for indie developers, students, and small engineering teams.")

    tier_col1, tier_col2 = st.columns(2)

    with tier_col1:
        st.markdown(
            """
            <div class="info-card" style="border: 2px solid #38bdf8;">
                <span class="badge-pill badge-privacy">Free & Open Source</span>
                <h3 style="margin-top: 10px;">Community Core</h3>
                <div style="font-size: 2.2rem; font-weight: 700; color: #f8fafc; margin: 12px 0;">$0 <span style="font-size: 0.9rem; color: #94a3b8;">/ forever</span></div>
                <p style="color: #94a3b8;">For indie hackers, solo developers, and computer science students.</p>
                <ul style="color: #cbd5e1; line-height: 1.8;">
                    <li>✅ 100% Local execution on your laptop</li>
                    <li>✅ Automatic secret & credential masking</li>
                    <li>✅ Multi-language stack trace extraction</li>
                    <li>✅ Offline heuristic rule mode included</li>
                    <li>✅ Markdown investigation report export</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tier_col2:
        st.markdown(
            """
            <div class="info-card" style="border: 2px solid #a855f7;">
                <span class="badge-pill badge-ai">Paid Convenience Layer</span>
                <h3 style="margin-top: 10px;">TraceLite for Teams</h3>
                <div style="font-size: 2.2rem; font-weight: 700; color: #f8fafc; margin: 12px 0;">$15 <span style="font-size: 0.9rem; color: #94a3b8;">/ seat / month</span></div>
                <p style="color: #94a3b8;">For small startups and engineering agencies needing shared crash triage.</p>
                <ul style="color: #cbd5e1; line-height: 1.8;">
                    <li>✨ <strong>Shared Team Workspace:</strong> Share sanitized triage reports without sending raw logs over Slack</li>
                    <li>✨ <strong>One-Click Issue Sync:</strong> Export directly to GitHub Issues, Linear, or Jira with repro steps</li>
                    <li>✨ <strong>CI/CD PR Bot:</strong> Automatically triages failed test logs in GitHub Actions</li>
                    <li>✨ <strong>Private Team Vault:</strong> Retain past investigation reports for post-mortems</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


# --- PAGE 5: PRIVACY & SECURITY ENGINE ---
elif st.session_state.nav_page == "🛡️ Privacy Engine":
    st.markdown("## 🛡️ Privacy by Design: Zero Data Leakage")
    st.markdown("Traditional cloud observability services require transmitting proprietary application logs to external servers. TraceLite AI keeps all processing local.")

    st.markdown(
        """
        <div class="info-card">
            <h3>🔒 What Gets Automatically Redacted?</h3>
            <p>TraceLite's <code>SecretMasker</code> continuously inspects log text using regex signatures before displaying output or packaging AI prompts:</p>
            <ul>
                <li><strong>OpenAI & AI API Keys:</strong> <code>sk-abcdef1234...</code> &rarr; <code>[REDACTED_OPENAI_KEY]</code></li>
                <li><strong>AWS Credentials:</strong> <code>AKIAIOSFODNN7EXAMPLE</code> &rarr; <code>[REDACTED_AWS_KEY]</code></li>
                <li><strong>GitHub Personal Tokens:</strong> <code>ghp_123456...</code> &rarr; <code>[REDACTED_GITHUB_TOKEN]</code></li>
                <li><strong>Bearer Auth Tokens:</strong> <code>Authorization: Bearer ey...</code> &rarr; <code>Bearer [REDACTED_BEARER_TOKEN]</code></li>
                <li><strong>Database Connection Strings:</strong> <code>postgres://user:password@host/db</code> &rarr; <code>postgres://user:[REDACTED_PWD]@host/db</code></li>
                <li><strong>Private Keys:</strong> <code>-----BEGIN PRIVATE KEY-----</code> blocks &rarr; <code>[REDACTED_PRIVATE_KEY]</code></li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- FOOTER ---
st.markdown(
    """
    <div class="app-footer">
        <div class="footer-links">
            <a href="https://github.com/Vaibhav-1819/tracelite_ai" target="_blank">⭐ GitHub Repository</a>
            <a href="https://github.com/Vaibhav-1819/tracelite_ai/blob/main/LICENSE" target="_blank">📄 MIT License</a>
            <a href="https://dev.to/challenges/hacktoberfest-week2-2026-10-12" target="_blank">🏆 Hacktoberfest 2026 AI Challenge</a>
            <a href="https://ollama.com" target="_blank">🦙 Ollama Runtime</a>
        </div>
        <p class="footer-text">
            <strong>TraceLite AI</strong> — Local-first log triage & stack trace investigation assistant powered by open-weight AI.
        </p>
        <p class="footer-text" style="font-size: 0.78rem; color: #475569;">
            Built with Space Grotesk typography, Streamlit, and Python. Zero cloud AI API fees.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
