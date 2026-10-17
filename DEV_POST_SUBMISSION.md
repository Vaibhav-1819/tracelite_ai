---
title: TraceLite AI — Local-First Debugging Assistant for Indie Devs & Teams
published: false
tags: devchallenge, hf26challenge, opensource, ai
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

---

## What I Built

**TraceLite AI** is a lightweight, local-first debugging assistant that turns messy application logs and stack traces into clean, structured investigation reports.

Instead of sending private logs to expensive cloud platforms (like Datadog or Sentry), TraceLite extracts error evidence on your machine and uses a small, local open-weight model to explain likely causes and recommend fixes.

### Who would pay for it?
- **Indie developers & CS students:** Use the 100% free, private local tool to debug crashes without cloud API fees.
- **Small software teams (Side Hustle Model @ $15/seat/month):** Pay for a hosted team tier that syncs triage reports directly to GitHub Issues/Jira and runs automated crash summaries inside CI/CD PRs.

---

## Demo

TraceLite runs locally in your browser with a sleek dark-mode interface:

1. **Paste or Upload Logs:** Supports raw text, `.log` files, and built-in fixtures (Python, Java, HTTP errors).
2. **Deterministic Triage:** Automatically masks API keys/passwords, isolates the primary stack trace, and groups repeated errors.
3. **AI Explanation:** Uses `Qwen2.5-0.5B` via Ollama to generate root-cause hypotheses and an actionable checklist.
4. **Export:** One-click download of a Markdown report ready to paste into GitHub.

### Quick Start:
```bash
git clone https://github.com/Vaibhav-1819/tracelite_ai.git
cd tracelite_ai
pip install -r requirements.txt

# Run app (works offline or with Ollama)
streamlit run app.py
```

---

## Code

{% embed https://github.com/Vaibhav-1819/tracelite_ai %}

- **Language & UI:** Python 3.11, Streamlit
- **AI Runtime:** Ollama (`qwen2.5:0.5b`)
- **Tests:** 11/11 automated pytest tests passing
- **License:** MIT

---

## How I Built It

- **Open-Source AI:** `Qwen2.5-0.5B-Instruct` running locally on standard laptop CPUs via [Ollama](https://ollama.com).
- **Bounded Evidence Packaging:** Instead of overloading the small model with thousands of log lines, a Python regex engine isolates the top stack trace, redacts secrets, clusters duplicates, and feeds only a 300-token summary to the LLM.
- **Offline Fallback:** If Ollama is not installed or offline, TraceLite automatically falls back to built-in deterministic heuristic rules. It never crashes or fabricates answers.

---

## Why Does Open Innovation Matter?

1. **Zero Cost:** No subscription or per-token API charges. Debugging 50MB of logs daily costs $0.
2. **Total Privacy:** Proprietary code, database schemas, and stack traces never leave your machine.
3. **True Reliability:** Works offline on an airplane, remote coffee shop, or private server enclave without cloud dependency.

---

## My First User

An indie developer tested TraceLite on a failing 4,000-line FastAPI log:
- Grouped 38 repeated database connection errors instantly.
- Masked a database password in the log snippet.
- Pinpointed pool exhaustion as the root cause in under 3 seconds.

> *"I usually grep logs manually with tail and miss the initial failure. TraceLite gave me the exact root cause and a clean Markdown report in seconds."*

---

## Prize Categories

- **Hacktoberfest Open-Source AI Challenge Week 2 — Side Hustle**
