# TraceLite AI — Local-First Debugging Assistant Powered by Open-Weight AI

*Submission for the DEV Open Source AI Side Hustle Challenge*

---

## What I Built

Debugging runtime errors in complex applications often feels like searching for a needle in a digital haystack. You trigger an error, open your terminal or container logs, and get bombarded by hundreds of lines of noise, unhandled exception traces, and repetitive warning messages.

To solve this, I built **TraceLite AI** — an open-source, local-first debugging assistant that ingests raw application logs and stack traces, extracts deterministic evidence, isolates primary root causes, and uses an open-weight language model (`Qwen2.5-0.5B-Instruct` via Ollama) to generate structured investigation reports with zero external API fees.

### Key Highlights:
- **100% Local & Cost-Free:** No OpenAI, Claude, or third-party cloud AI subscriptions required. Runs on standard CPU hardware.
- **Privacy by Design:** Automatically redacts sensitive secrets (API keys, JWTs, AWS credentials, database passwords) before parsing.
- **Deterministic Log & Trace Extraction:** Automatically detects Python tracebacks, Java JVM exception chains, Node.js traces, and Go panics, clustering recurring error templates.
- **Evidence-First Transparency:** Explicitly distinguishes verified facts from AI-generated hypotheses. TraceLite never claims to have executed code or verified a fix.
- **Graceful Offline Fallback:** If Ollama is offline or uninstalled, TraceLite continues running with its deterministic heuristic diagnostic engine without breaking.
- **One-Click Markdown Export:** Download or copy GitHub-ready markdown investigation reports.

---

## Architecture & How It Works

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

### 1. Bounded Context Packaging
Small open-weight models (like Qwen2.5-0.5B) have limited context windows and can easily be distracted by raw log noise. Instead of dumping megabytes of text into the prompt, TraceLite extracts:
- Primary isolated error signature
- Cleaned stack trace frames (capped to top and bottom frames)
- Top 3 recurring error clusters with counts
- Event count and timeline distribution

### 2. Guardrails & Evidence Anchoring
The prompt constrains the model to structured JSON output and mandates that every hypothesis cite concrete line numbers and exception types extracted by the deterministic parser.

---

## Demo & Walkthrough

TraceLite includes a deliberately broken billing service (`demo_app.py`) that produces an unhandled `ZeroDivisionError`:

```python
def calculate_average_discount(invoices, total_units):
    total_discount_amount = sum(inv.get("discount", 0.0) for inv in invoices)
    # Bug: zero units sold produces ZeroDivisionError
    discount_ratio = total_discount_amount / total_units
    return discount_ratio
```

When piped into TraceLite AI:
1. **Masker:** Detects and redacts simulated authorization token `sk-9f82...` -> `[REDACTED_OPENAI_KEY]`.
2. **Parser:** Isolates `ZeroDivisionError: division by zero` in `demo_app.py:L26`.
3. **AI Engine:** Generates root causes (`total_units evaluates to 0 due to empty sales dataset`) and recommended defensive checks (`if total_units > 0:`).
4. **Export:** One-click download of the complete Markdown investigation report.

---

## Tech Stack
- **Frontend / Interface:** Streamlit (custom dark-mode glassmorphic theme)
- **Log Engine:** Python 3.10+ (dataclasses, regex clustering, datetime aggregation)
- **Local AI Inference:** Ollama runtime with `Qwen2.5-0.5B-Instruct`
- **Testing:** Pytest (11 unit tests covering parsers, maskers, AI fallbacks, and exporters)

---

## Repository & Links

- **GitHub Repository:** [https://github.com/Vaibhav-1819/tracelite_ai](https://github.com/Vaibhav-1819/tracelite_ai)
- **License:** MIT License
- **Fixtures & Demos:** Included in `/fixtures` and `demo_app.py`
