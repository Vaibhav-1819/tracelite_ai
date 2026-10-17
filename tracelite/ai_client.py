"""
TraceLite AI - AI Inference Client & Fallback Engine
Communicates with local Ollama instance (e.g., Qwen2.5-0.5B-Instruct)
and provides deterministic fallback when Ollama is unavailable.
"""

import json
import logging
from typing import Optional, Dict, Any, List, Tuple
import requests

from .models import DeterministicAnalysis, AIHypothesis, StackTrace

logger = logging.getLogger(__name__)

# Heuristic diagnostic knowledge base for graceful offline fallback
KNOWN_PATTERNS = {
    "zerodivisionerror": {
        "title": "Division by Zero in Arithmetic Operation",
        "explanation": "The program attempted to divide a number by zero or a variable evaluated to zero at runtime.",
        "causes": [
            "Denominator variable is initialized or reset to 0",
            "Missing check before division (e.g., count == 0 or len(items) == 0)",
            "Unexpected empty dataset or aggregate query returning zero count",
        ],
        "steps": [
            "Inspect the line where the division operation occurs",
            "Add defensive conditional check (e.g., `if denominator != 0:`)",
            "Set a fallback default value or raise a custom domain exception",
            "Trace back where the denominator value was computed or fetched",
        ],
        "confidence": "High (Deterministic pattern match on Python ZeroDivisionError)",
    },
    "nullpointerexception": {
        "title": "Null Object Reference Dereference",
        "explanation": "A method or field was invoked on an object reference that is currently null in JVM execution.",
        "causes": [
            "Uninitialized service dependency or un-injected Spring bean",
            "Repository or database lookup returned null for missing ID",
            "Missing null-check on optional API request payload property",
        ],
        "steps": [
            "Check line number from the top stack frame",
            "Inspect which variable in the chained call evaluated to null",
            "Use `Optional<T>`, null checks, or `@NotNull` annotations",
            "Verify bean wiring or dependency injection configuration",
        ],
        "confidence": "High (Deterministic pattern match on Java NullPointerException)",
    },
    "connectionrefused": {
        "title": "Network Connection Refused",
        "explanation": "The application attempted to establish a TCP connection to a host/port where no service is listening.",
        "causes": [
            "Target database, cache, or microservice is not running",
            "Incorrect host name or port configured in environment variables",
            "Firewall or container network bridge blocking outbound socket connection",
        ],
        "steps": [
            "Verify the target service (PostgreSQL, Redis, HTTP API) is active",
            "Check connection string host and port settings",
            "Test socket reachability using `telnet` or `curl` from the application container",
        ],
        "confidence": "Moderate (Inferred from connection refused socket error)",
    },
    "429": {
        "title": "HTTP Rate Limit Exceeded (429)",
        "explanation": "The upstream server rejected requests due to exceeding rate limits or quota thresholds.",
        "causes": [
            "High burst of concurrent requests without throttling or batching",
            "Missing exponential backoff and jitter in API retry loop",
            "Shared IP address or API key exhausted allowed request quota",
        ],
        "steps": [
            "Inspect rate limiting headers (`Retry-After`, `X-RateLimit-Reset`)",
            "Implement client-side exponential backoff with jitter",
            "Add local caching or queuing to reduce upstream call frequency",
        ],
        "confidence": "High (Deterministic HTTP 429 status match)",
    },
    "500": {
        "title": "Internal Server Error (500)",
        "explanation": "The upstream web server encountered an unhandled exception or crash while processing the request.",
        "causes": [
            "Unhandled application exception in backend endpoint handler",
            "Database transaction deadlock or query timeout",
            "Downstream microservice dependency failure",
        ],
        "steps": [
            "Check backend server logs around the timestamp of the 500 error",
            "Inspect error response body or tracing headers (e.g., `traceparent`, `X-Request-ID`)",
            "Add structured error boundary and return informative 4xx response if client input is invalid",
        ],
        "confidence": "Moderate (Generic HTTP 500 status indicator)",
    },
}


class AIClient:
    """Manages Ollama API inference with bounded evidence packaging and fallback."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "qwen2.5:0.5b",
        timeout_seconds: float = 8.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout_seconds

    def check_ollama_available(self) -> Tuple[bool, str, List[str]]:
        """Checks if Ollama endpoint is running and responding."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=1.5)
            if resp.status_code == 200:
                models = [m.get("name", "") for m in resp.json().get("models", [])]
                return True, f"Ollama is online ({len(models)} models available)", models
            return False, f"Ollama returned HTTP {resp.status_code}", []
        except Exception as e:
            return False, f"Ollama unavailable at {self.base_url}", []

    def build_evidence_package(self, analysis: DeterministicAnalysis) -> Dict[str, Any]:
        """Creates a compact, bounded evidence payload suitable for a small open-weight LLM."""
        evidence: Dict[str, Any] = {
            "total_lines": analysis.total_lines,
            "error_count": analysis.error_count,
            "primary_error": analysis.primary_error or "Unknown error",
            "stack_traces": [],
            "top_error_patterns": [],
        }

        # Include up to 2 primary stack traces (bounded length)
        for st in analysis.stack_traces[:2]:
            evidence["stack_traces"].append({
                "language": st.language,
                "exception_type": st.exception_type,
                "exception_message": st.exception_message,
                "frames_count": len(st.frames),
                "top_frames": st.frames[:4],
                "bottom_frame": st.frames[-1] if st.frames else "",
            })

        # Include top 3 recurring error signatures
        for eg in analysis.error_groups[:3]:
            evidence["top_error_patterns"].append({
                "sample": eg.sample_message[:120],
                "count": eg.count,
                "first_line": eg.first_seen_line,
            })

        return evidence

    def investigate(self, analysis: DeterministicAnalysis) -> AIHypothesis:
        """
        Executes investigation. Tries Ollama first; if unavailable or failing,
        gracefully uses deterministic heuristic analysis.
        """
        is_online, _, available_models = self.check_ollama_available()

        if is_online:
            try:
                hypothesis = self._call_ollama(analysis)
                if hypothesis:
                    return hypothesis
            except Exception as e:
                logger.warning(f"Ollama inference failed: {e}. Falling back to heuristics.")

        # Graceful Fallback
        return self._generate_heuristic_hypothesis(analysis)

    def _call_ollama(self, analysis: DeterministicAnalysis) -> Optional[AIHypothesis]:
        """Sends bounded evidence package to Ollama."""
        evidence = self.build_evidence_package(analysis)

        system_prompt = (
            "You are TraceLite AI, an open-source log investigation assistant.\n"
            "Analyze the provided log evidence. Distinguish observed facts from hypotheses.\n"
            "You have NOT executed any code or verified a fix.\n"
            "Respond ONLY in valid JSON matching this exact structure:\n"
            "{\n"
            '  "title": "Short descriptive title of the issue",\n'
            '  "explanation": "Clear plain-language explanation of what happened",\n'
            '  "likely_causes": ["Plausible cause 1", "Plausible cause 2"],\n'
            '  "suggested_steps": ["Ordered diagnostic step 1", "Ordered diagnostic step 2", "Ordered diagnostic step 3"],\n'
            '  "confidence_statement": "Statement regarding evidence clarity and uncertainty"\n'
            "}"
        )

        user_prompt = (
            f"LOG EVIDENCE PACKAGE:\n"
            f"{json.dumps(evidence, indent=2)}\n\n"
            "Provide your investigation in the requested JSON format."
        )

        payload = {
            "model": self.model_name,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2,
                "num_predict": 400,
            },
        }

        resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
        if resp.status_code != 200:
            return None

        result_text = resp.json().get("response", "")
        parsed_json = self._parse_json_safely(result_text)
        if not parsed_json:
            return None

        return AIHypothesis(
            title=str(parsed_json.get("title", "Error Analysis")),
            explanation=str(parsed_json.get("explanation", "Logs indicate runtime error.")),
            likely_causes=[str(c) for c in parsed_json.get("likely_causes", [])],
            suggested_steps=[str(s) for s in parsed_json.get("suggested_steps", [])],
            confidence_statement=str(
                parsed_json.get("confidence_statement", "Analysis generated by local model based on log snippets.")
            ),
            model_name=self.model_name,
            is_fallback=False,
            evidence_referenced=[analysis.primary_error or "Log evidence"],
        )

    def _parse_json_safely(self, text: str) -> Optional[Dict[str, Any]]:
        """Extracts and parses JSON from model output."""
        try:
            return json.loads(text.strip())
        except Exception:
            pass

        # Try regex to locate first { and last }
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start : end + 1])
        except Exception:
            pass

        return None

    def _generate_heuristic_hypothesis(self, analysis: DeterministicAnalysis) -> AIHypothesis:
        """Deterministic heuristic fallback when Ollama is offline."""
        primary = (analysis.primary_error or "").lower()

        # Check known pattern rules
        matched_kb = None
        for key, kb in KNOWN_PATTERNS.items():
            if key in primary:
                matched_kb = kb
                break

        if not matched_kb:
            # Check stack traces
            for st in analysis.stack_traces:
                for key, kb in KNOWN_PATTERNS.items():
                    if key in st.exception_type.lower():
                        matched_kb = kb
                        break
                if matched_kb:
                    break

        if matched_kb:
            return AIHypothesis(
                title=matched_kb["title"],
                explanation=matched_kb["explanation"],
                likely_causes=matched_kb["causes"],
                suggested_steps=matched_kb["steps"],
                confidence_statement=f"{matched_kb['confidence']} [Offline Mode]",
                model_name="deterministic-heuristics",
                is_fallback=True,
                evidence_referenced=[analysis.primary_error or "Detected pattern"],
            )

        # Generic fallback
        title = "Runtime Exception Detected" if analysis.error_count > 0 else "Log Inspection Complete"
        explanation = (
            f"Encountered {analysis.error_count} error event(s) across {analysis.total_lines} log lines. "
            f"Primary failure: '{analysis.primary_error or 'No critical exceptions isolated'}'. "
            "Evidence indicates an unhandled error condition during execution."
        )
        causes = [
            "Unexpected null, missing, or malformed input data",
            "External dependency, database, or network socket timeout",
            "Application unhandled state transition or configuration discrepancy",
        ]
        steps = [
            "Inspect the stack trace line numbers and surrounding context lines",
            "Verify environment configuration and database connectivity",
            "Reproduce the failing transaction locally with debug logging enabled",
        ]

        return AIHypothesis(
            title=title,
            explanation=explanation,
            likely_causes=causes,
            suggested_steps=steps,
            confidence_statement="Deterministic heuristic analysis (Ollama offline). Hypotheses based on log structure.",
            model_name="deterministic-heuristics",
            is_fallback=True,
            evidence_referenced=[analysis.primary_error or "Log lines"],
        )


Tuple_Status = tuple[bool, str, List[str]]
