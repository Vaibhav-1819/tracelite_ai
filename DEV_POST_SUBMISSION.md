---
title: How I Built TraceLite AI: A Local-First Debugging Assistant That Saves You From Log Hell
published: false
tags: devchallenge, hf26challenge, opensource, ai
cover_image: https://raw.githubusercontent.com/Vaibhav-1819/tracelite_ai/main/tracelite_cover.jpg
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

---

## What I Built

If you've ever stared at a 3,000-line terminal wall of raw logs after a midnight deployment crash, you know the exact pain I’m talking about. 

You scroll frantically, trying to figure out which line is the actual root cause and which 200 lines are just cascading warning noise. Most small teams and indie devs I know don't have $300/month to drop on enterprise observability suites like Datadog or Dynatrace. And even if you do, sending proprietary server logs containing user IDs and database queries to external cloud AI APIs is a massive privacy risk.

I built **TraceLite AI** to solve this.

It is a lightweight, local-first debugging companion. You paste in an unreadable stack trace or upload a raw `.log` file, and TraceLite:
1. **Redacts secrets instantly** (stripping out auth headers, OpenAI keys, and database passwords before anything touches memory).
2. **Deterministically clusters the noise** (grouping repeated error templates and isolating the actual failure point).
3. **Runs a local open-weight AI model (`Qwen2.5-0.5B`)** via Ollama right on your laptop CPU to explain *why* it crashed and generate an actionable fix checklist.
4. **Exports a clean Markdown report** that you can drop directly into a GitHub issue or pull request.

```
Raw Logs ──> Secret Masker ──> Deterministic Parser ──> Bounded Evidence Package
                                                                │
                            ┌───────────────────────────────────┴───────────────────────────────────┐
                            ▼                                                                       ▼
             Ollama Runtime (Qwen2.5-0.5B)                                          Offline Heuristic Fallback
                            │                                                                       │
                            └───────────────────────────────────┬───────────────────────────────────┘
                                                                ▼
                                                    Evidence-First Investigation
                                                    & Markdown Report Export
```

### Who would pay for this? (The Side Hustle Thesis)
I designed TraceLite around an **open-core model**:
- **100% Free & Open Source Core:** The local CLI and standalone Streamlit web app will always remain free. Solo builders and CS students shouldn't have to pay to debug their side projects.
- **Hosted Team Convenience Layer ($12–$19/month per team):** Small agencies and startups don't want to pass raw logs around Slack. The paid tier will offer:
  - A shared team investigation inbox with privacy-scrubbed crash histories.
  - One-click GitHub & Linear integrations that convert a triage report into an assigned bug ticket.
  - A GitHub Actions CI/CD bot that automatically runs TraceLite on failed test logs and posts a human explanation on the pull request.

---

## Demo

TraceLite AI features a modern, responsive web application styled with **Space Grotesk typography**, glassmorphic card elements, a floating top Navbar, and a persistent Footer with 5 dedicated sections:
- **🔍 Log Investigator:** Live triage console, one-click fixtures, stack trace isolation, and Markdown exporter.
- **🚀 Architecture:** Interactive breakdown of the bounded evidence packaging pipeline.
- **📖 Docs & CLI:** Setup instructions, `demo_app.py` walkthrough, and automated testing guide.
- **💼 Side Hustle & Pricing:** Comparison between the free Community Core and the paid Team Convenience Layer ($15/seat/mo).
- **🛡️ Privacy Engine:** Deep-dive into automated regex masking of API keys, tokens, and database passwords.

Here is how the end-to-end investigation workflow looks in practice:

### 1. Ingesting Logs & Isolating Errors
Paste raw logs, upload a file, or click a sample fixture. TraceLite instantly runs secret masking, isolates the primary error in a clear red banner, and prepares the triage report:

![Raw log input and isolated error banner](https://raw.githubusercontent.com/Vaibhav-1819/tracelite_ai/main/images/logs.png)

### 2. Deterministic Metrics & Stack Trace Extraction
The engine parses multi-language stack traces (Python, Java JVM, Node.js, Go), computes line-by-line metrics, and reveals surrounding context lines:

![Deterministic metrics and stack trace extraction](https://raw.githubusercontent.com/Vaibhav-1819/tracelite_ai/main/images/analysis.png)

### 3. AI Investigation & Diagnostic Checklist
The local open-weight model (`Qwen2.5-0.5B`) provides plain-language explanations, identifies plausible root causes, and generates an ordered diagnostic checklist:

![AI Investigation and diagnostic checklist](https://raw.githubusercontent.com/Vaibhav-1819/tracelite_ai/main/images/checklist.png)

---

### Running It Yourself
You don't need a GPU. It runs on any standard laptop:

```bash
# 1. Clone the repo
git clone https://github.com/Vaibhav-1819/tracelite_ai.git
cd tracelite_ai

# 2. Install requirements
pip install -r requirements.txt

# 3. (Optional) Run Ollama if you want the local LLM enabled
ollama run qwen2.5:0.5b

# 4. Fire up the dashboard
streamlit run app.py
```

*Tip: If you don't have Ollama installed, don't worry! TraceLite automatically activates its built-in heuristic engine so you get immediate diagnostic reports without installing anything extra.*

---

## Code

{% embed https://github.com/Vaibhav-1819/tracelite_ai %}

The entire codebase is open-source under the MIT license:
- [`tracelite/parser.py`](https://github.com/Vaibhav-1819/tracelite_ai/blob/main/tracelite/parser.py): The deterministic regex engine that parses Python, Java (JVM stack traces with `Caused by:`), JavaScript/Node.js, and Go panics.
- [`tracelite/masker.py`](https://github.com/Vaibhav-1819/tracelite_ai/blob/main/tracelite/masker.py): The privacy filter catching AWS keys, Bearer tokens, DB credentials, and API secrets.
- [`tracelite/ai_client.py`](https://github.com/Vaibhav-1819/tracelite_ai/blob/main/tracelite/ai_client.py): Ollama integration with bounded evidence packaging and deterministic offline fallback.
- [`app.py`](https://github.com/Vaibhav-1819/tracelite_ai/blob/main/app.py): The Streamlit web interface styled with Space Grotesk typography and custom glassmorphism.
- [`tests/`](https://github.com/Vaibhav-1819/tracelite_ai/tree/main/tests): 11 unit tests covering all parsers and failure edge cases (`pytest` passes 100%).

---

## How I Built It

### The Open-Source AI Architecture
I deliberately avoided heavyweight models. Instead, I paired a **small open-weight language model (`Qwen2.5-0.5B-Instruct`)** with a fast Python preprocessing pipeline:

1. **The Context Problem:** Small 0.5B models get confused if you throw 5,000 lines of raw logs at them. Their context windows choke, latency spikes, and they start hallucinating.
2. **The Bounded Evidence Solution:** I built a deterministic parser that acts as a bouncer. It strips out timestamps, masks sensitive tokens, clusters recurring messages (e.g. converting `POST /checkout 500` repeated 40 times into a single line with count=40), and sends only a clean, 300-token evidence summary to the model.
3. **Strict JSON Schema Guardrails:** The prompt forces the model to respond strictly in structured JSON, returning an explanation, plausible root causes, ordered diagnostic steps, and an uncertainty statement.
4. **Graceful Fallback:** If Ollama is sleeping or not installed, TraceLite doesn't crash. It seamlessly routes through a deterministic heuristic rule engine that diagnoses common errors (`ZeroDivisionError`, `NullPointerException`, HTTP 429, HTTP 500) with honest attribution.

---

## Why Does Open Innovation Matter?

Building this project made one thing crystal clear: **some problems should never be handed to closed cloud APIs.**

1. **Real Data Privacy:** Debugging server crashes means touching sensitive data: internal hostnames, database connection strings, and user payloads. Feeding raw production logs into a closed third-party cloud API is an unacceptable compliance risk for most developers. Open-weight models running on `localhost` keep your data where it belongs.
2. **Zero Marginal Cost:** If I had to pay $0.02 per OpenAI API call every time I tested a log parser against large logs, building this side hustle would have cost me money before getting my first user. With open-weight AI, I ran thousands of test parses for exactly $0.
3. **Resilience & Independence:** Closed APIs can change pricing, deprecate model versions, or suffer outages during your own production downtime. With `Qwen2.5` and Ollama, my debugging tool works on a plane at 30,000 feet with zero Wi-Fi.

---

## My First User

To test TraceLite in the real world, I asked an indie developer friend to test-drive it on a tricky issue in their FastAPI application. Their container logs were drowning in sporadic 500 errors.

**What TraceLite did in under 3 seconds:**
- Stripped their PostgreSQL password from the raw connection string before displaying anything.
- Collapsed 42 repetitive connection failure lines into a single cluster.
- Pinpointed that their async connection pool was running out of open slots during checkout surges.

**Their reaction:**
> *"Usually when a server goes down, I'm grepping terminal windows with `tail -n 100` and piecing together the timeline in my head. TraceLite pulled the exact culprit straight out of the noise and gave me a checklist I could follow right away. The fact that it runs locally without uploading my database errors to the cloud is a game changer."*

---

## Over to You: Let's Discuss in the Comments!

I'd love to hear your thoughts and war stories:
- **What is the nastiest, most cryptic stack trace you’ve had to troubleshoot recently?**
- **Have you experimented with small open-weight models (like Qwen2.5 0.5B or Llama 3.2 1B) for local development tools?**
- **What integration would you find most useful:** a VS Code extension, a GitHub Actions PR bot, or a CLI pipe (`my_cmd 2>&1 | tracelite`)?

If you found this project helpful or interesting, feel free to **share it with your team, coworkers, or developer community**, and star the repo on **[GitHub](https://github.com/Vaibhav-1819/tracelite_ai)**! Drop any questions or feedback below—I'll be hanging out in the comments to reply to every single one.

---

## Prize Categories

- **Primary Track:** Hacktoberfest Open-Source AI Challenge Week 2 — Side Hustle
- **Open-Source Innovation Track:** Demonstrating practical, local-first inference using `Qwen2.5-0.5B-Instruct` on everyday hardware with zero API fees.
