# 🔍 TraceLite AI

> **Lightweight, local-first debugging assistant that converts raw application logs and stack traces into structured, actionable investigation reports.**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io)
[![Ollama](https://img.shields.io/badge/AI%20Runtime-Ollama-black.svg)](https://ollama.com)
[![Model](https://img.shields.io/badge/Open--Weight%20Model-Qwen2.5--0.5B-purple.svg)](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: Pytest](https://img.shields.io/badge/Tests-11%2F11%20Passing-brightgreen.svg)]()

---

## 💡 Overview

When applications crash, developers are often confronted with massive walls of logs: repeated exceptions, noise, obscure JVM traces, or unhandled Python errors. Traditional observability suites are complex, expensive, and require transmitting proprietary server logs to third-party clouds.

**TraceLite AI** solves this with a **zero-cost, local-first architecture**:
1. **Deterministic Parsing & Extraction:** Fast Python regex engine parses multi-language stack traces (Python, Java, Node.js, Go), clusters recurring error signatures, normalizes dynamic variables, and builds event timelines.
2. **Automated Secret & Credential Redaction:** API keys (OpenAI, AWS, GitHub), bearer tokens, database passwords, and JWTs are automatically stripped before analysis or export.
3. **Open-Weight AI Investigation:** An ultra-lightweight open-weight LLM (`Qwen2.5-0.5B-Instruct` via Ollama) provides plain-language explanations, root-cause hypotheses, and ordered debugging steps.
4. **Graceful Fallback:** Operates 100% offline with deterministic heuristics if Ollama is not installed or unreachable.
5. **Evidence-First Markdown Export:** Downloads clean reports separating verified facts from AI hypotheses, ready to paste into GitHub issues or pull requests.

---

## 🏗️ Architecture

```
                                  ┌───────────────────────────┐
                                  │      Raw Application      │
                                  │   Logs & Stack Traces     │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │    Secret & PII Masker    │  ──> Redacts API keys & Passwords
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │   Deterministic Parser    │
                                  │  • Stack trace isolation  │
                                  │  • Message clustering     │
                                  │  • Timeline aggregation   │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │  Bounded Evidence Package │
                                  └──────┬─────────────┬──────┘
                                         │             │
                    [Ollama Online]      │             │  [Ollama Offline]
                                         ▼             ▼
                           ┌─────────────────┐   ┌────────────────────────┐
                           │   Ollama LLM    │   │ Deterministic Heuristic│
                           │ (Qwen2.5-0.5B)  │   │      Rule Engine       │
                           └────────┬────────┘   └───────────┬────────────┘
                                    │                        │
                                    └───────────┬────────────┘
                                                ▼
                                  ┌───────────────────────────┐
                                  │   Evidence-First Report   │
                                  │  • Primary error isolated │
                                  │  • Plausible hypotheses   │
                                  │  • Diagnostic steps       │
                                  │  • Markdown export        │
                                  └───────────────────────────┘
```

---

## ✨ Features

- **Multi-Language Stack Trace Parser:** Native support for Python tracebacks, Java JVM exception chains (`Caused by:`), JavaScript/Node.js stack traces, and Go panics.
- **Error Template Clustering:** Normalizes UUIDs, memory addresses, IP addresses, and timestamps to group recurring errors and show accurate frequency distributions.
- **Privacy-by-Design:** No logs ever leave your local machine. Built-in `SecretMasker` redacts credentials before display or prompt assembly.
- **Local AI Inference:** Zero API fees, zero subscriptions. Runs on ordinary consumer laptops with CPU-only inference using `Qwen2.5-0.5B-Instruct`.
- **Offline Heuristic Fallback:** If Ollama is offline or uninstalled, TraceLite continues to provide deterministic root-cause heuristics and diagnostic checklists without breaking.
- **One-Click Sample Fixtures:** Built-in test cases for Python `ZeroDivisionError`, Java Spring Boot `NullPointerException`, and HTTP 500 / 429 rate limit events.
- **Export Ready:** One-click download of GitHub-flavored Markdown investigation reports.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- (Optional, recommended for AI mode) [Ollama](https://ollama.com)

### 2. Installation

Clone this repository and install dependencies:

```bash
git clone https://github.com/vaibhav/tracelite-ai.git
cd tracelite-ai

# Install dependencies
pip install -r requirements.txt
```

### 3. (Optional) Run Local AI Model with Ollama

If you want AI-generated hypotheses in addition to deterministic analysis, pull and run the ultra-lightweight `qwen2.5:0.5b` model (under 400MB):

```bash
ollama run qwen2.5:0.5b
```

> **Note:** If Ollama is not running, TraceLite automatically activates its **Deterministic Heuristic Engine** with zero configuration required!

### 4. Launch the Web Application

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 🧪 Running the Demo Scenario

TraceLite AI includes a deliberately broken billing service application (`demo_app.py`) that produces an unhandled `ZeroDivisionError` alongside a simulated secret API key:

```bash
# Run the demo script to produce the crash
python demo_app.py
```

1. Open `http://localhost:8501`.
2. In the sidebar under **Quick-Load Sample Fixtures**, click **🐍 Python ZeroDivisionError**.
3. Click **🔍 Investigate Logs**.
4. Observe:
   - **Isolated primary error:** `ZeroDivisionError: division by zero` in `demo_app.py:L26`.
   - **Secret Redaction:** `sk-9f82...` automatically replaced with `[REDACTED_OPENAI_KEY]`.
   - **Root Cause Hypotheses:** Highlights `total_units == 0` due to empty inventory.
   - **Diagnostic Checklist:** Step-by-step remediation guide.
   - **Export Report:** Go to the **📥 Export Report** tab to download the investigation as `.md`.

---

## 🔬 Automated Tests

Run the comprehensive pytest suite covering parsers, secret masking, AI bounded packaging, and markdown exporter:

```bash
pytest -v
```

```text
tests/test_ai_client.py::test_ai_fallback_on_zerodivision PASSED
tests/test_ai_client.py::test_bounded_evidence_package PASSED
tests/test_exporter.py::test_markdown_report_export PASSED
tests/test_masker.py::test_mask_openai_key PASSED
tests/test_masker.py::test_mask_aws_key PASSED
tests/test_masker.py::test_mask_bearer_token PASSED
tests/test_masker.py::test_mask_password_and_db_uri PASSED
tests/test_parser.py::test_empty_log PASSED
tests/test_parser.py::test_python_zerodivision_fixture PASSED
tests/test_parser.py::test_java_nullpointer_fixture PASSED
tests/test_parser.py::test_http_server_errors_fixture PASSED

============================= 11 passed in 4.70s ==============================
```

---

## ⚖️ Limitations & Ethical AI Disclosure

- **Evidence vs Hypotheses:** AI explanations are generated as diagnostic hypotheses based on bounded log evidence. TraceLite **does not execute code, modify repositories, or guarantee root-cause certainty**.
- **Model Hallucination:** Even small open-weight models may generate inaccurate explanations. Always review the extracted stack trace evidence before taking actions.
- **Log Boundaries:** Log inputs above 50,000 lines are truncated to maintain browser performance and bounded context windows.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
