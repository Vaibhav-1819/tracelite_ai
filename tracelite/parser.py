"""
TraceLite AI - Deterministic Log Parser and Analysis Engine
Extracts stack traces, detects error patterns, groups repeated messages, and builds timeline.
"""

import re
from collections import defaultdict
from typing import List, Tuple, Optional, Dict
from datetime import datetime

from .models import (
    LogLevel,
    ParsedLogLine,
    StackTrace,
    ErrorGroup,
    TimelinePoint,
    DeterministicAnalysis,
)
from .masker import SecretMasker

# Timestamp extraction regexes
TIMESTAMP_PATTERNS = [
    # ISO8601: 2026-10-18T10:15:30.123 or 2026-10-18 10:15:30,123
    re.compile(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[\.,]\d+)?)'),
    # Slash date: 2026/10/18 10:15:30
    re.compile(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})'),
    # Common log / Apache format: 18/Oct/2026:10:15:30
    re.compile(r'(\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2})'),
    # Syslog: Oct 18 10:15:30
    re.compile(r'([A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'),
]

# Log level indicators
LOG_LEVEL_PATTERN = re.compile(
    r'\b(CRITICAL|FATAL|ERROR|WARN|WARNING|INFO|DEBUG|TRACE)\b',
    re.IGNORECASE,
)

# HTTP error status codes (4xx, 5xx)
HTTP_ERROR_PATTERN = re.compile(r'\b(HTTP/\d\.\d[^\d]+)?(4\d{2}|5\d{2})\b')

# Normalization patterns for grouping repeated messages
NORMALIZE_RULES = [
    (re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'), '<UUID>'),
    (re.compile(r'\b0x[0-9a-fA-F]+\b'), '<ADDR>'),
    (re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), '<IP>'),
    (re.compile(r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[\.,]\d+)?\b'), '<TIMESTAMP>'),
    (re.compile(r'\b\d+\b'), '<NUM>'),
    (re.compile(r'\s+'), ' '),
]


class LogParser:
    """Deterministic parser for application logs and multi-language stack traces."""

    def __init__(self, masker: Optional[SecretMasker] = None):
        self.masker = masker or SecretMasker()

    def parse(self, raw_content: str, max_lines: int = 50000) -> DeterministicAnalysis:
        """
        Parses raw log text into a structured DeterministicAnalysis.
        Truncates if lines exceed max_lines.
        """
        if not raw_content or not raw_content.strip():
            return DeterministicAnalysis(
                total_lines=0,
                error_count=0,
                warning_count=0,
                stack_traces=[],
                error_groups=[],
                timeline=[],
                primary_error=None,
                masked_secrets_count=0,
            )

        # Normalize line endings
        normalized_content = raw_content.replace('\r\n', '\n').replace('\r', '\n')
        raw_lines = normalized_content.split('\n')

        # Bounds check
        if len(raw_lines) > max_lines:
            raw_lines = raw_lines[:max_lines]

        # Mask secrets
        clean_lines, masked_count = self.masker.mask_lines(raw_lines)

        # Parse individual lines
        parsed_lines: List[ParsedLogLine] = []
        error_count = 0
        warning_count = 0

        for idx, (raw, clean) in enumerate(zip(raw_lines, clean_lines), start=1):
            ts = self._extract_timestamp(clean)
            lvl = self._extract_log_level(clean)

            is_err = lvl in (LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.FATAL)
            if not is_err and self._contains_error_indicator(clean):
                is_err = True

            if is_err:
                error_count += 1
            elif lvl in (LogLevel.WARN, LogLevel.WARNING):
                warning_count += 1

            parsed_lines.append(
                ParsedLogLine(
                    line_number=idx,
                    raw_text=raw,
                    clean_text=clean,
                    timestamp=ts,
                    level=lvl,
                    message=clean.strip(),
                    is_error=is_err,
                )
            )

        # Extract stack traces (Python, Java, Node.js, Go)
        stack_traces = self._extract_stack_traces(parsed_lines)

        # Error grouping & signature clustering
        error_groups = self._cluster_error_groups(parsed_lines)

        # Build timeline
        timeline = self._build_timeline(parsed_lines)

        # Identify primary error
        primary_error = None
        if stack_traces:
            primary_error = f"{stack_traces[0].exception_type}: {stack_traces[0].exception_message}".strip(": ")
        elif error_groups:
            primary_error = error_groups[0].sample_message
        elif error_count > 0:
            for pl in parsed_lines:
                if pl.is_error:
                    primary_error = pl.message
                    break

        return DeterministicAnalysis(
            total_lines=len(parsed_lines),
            error_count=error_count,
            warning_count=warning_count,
            stack_traces=stack_traces,
            error_groups=error_groups,
            timeline=timeline,
            primary_error=primary_error,
            masked_secrets_count=masked_count,
        )

    def _extract_timestamp(self, text: str) -> Optional[str]:
        for pat in TIMESTAMP_PATTERNS:
            match = pat.search(text)
            if match:
                return match.group(1)
        return None

    def _extract_log_level(self, text: str) -> LogLevel:
        match = LOG_LEVEL_PATTERN.search(text)
        if match:
            return LogLevel.from_string(match.group(1))
        return LogLevel.UNKNOWN

    def _contains_error_indicator(self, text: str) -> bool:
        lower = text.lower()
        if "exception" in lower or "fatal" in lower or "traceback" in lower:
            return True
        if HTTP_ERROR_PATTERN.search(text):
            return True
        return False

    def _extract_stack_traces(self, lines: List[ParsedLogLine]) -> List[StackTrace]:
        """Detects Python, Java, JavaScript, and Go stack traces."""
        traces: List[StackTrace] = []
        n = len(lines)
        i = 0

        while i < n:
            line_text = lines[i].clean_text

            # 1. Python Traceback
            if "Traceback (most recent call last):" in line_text:
                start_line = lines[i].line_number
                frame_lines = []
                j = i + 1
                while j < n:
                    curr = lines[j].clean_text
                    if curr.startswith('  File ') or (curr.startswith('    ') and not re.match(r'^[A-Z][a-zA-Z0-9_]*Error:', curr.strip())):
                        frame_lines.append(curr)
                        j += 1
                    elif re.match(r'^[a-zA-Z0-9_\.]*(Error|Exception|Interrupt|Exit|AssertionError):', curr.strip()) or (curr and not curr.startswith(' ')):
                        # Final exception line
                        frame_lines.append(curr)
                        exc_parts = curr.strip().split(":", 1)
                        exc_type = exc_parts[0].strip()
                        exc_msg = exc_parts[1].strip() if len(exc_parts) > 1 else ""
                        end_line = lines[j].line_number
                        raw_trace = "\n".join(lines[k].clean_text for k in range(i, j + 1))
                        traces.append(
                            StackTrace(
                                start_line=start_line,
                                end_line=end_line,
                                language="python",
                                exception_type=exc_type,
                                exception_message=exc_msg,
                                frames=frame_lines[:-1],
                                raw_text=raw_trace,
                            )
                        )
                        i = j
                        break
                    else:
                        break
                i += 1
                continue

            # 2. Java Stack Trace
            # e.g.: Exception in thread "main" java.lang.NullPointerException: Cannot invoke ...
            # or com.example.MyException: something
            java_exc_match = re.search(r'(?:Exception in thread "[^"]*"\s+)?([a-zA-Z_][a-zA-Z0-9_\.]*(?:Exception|Error)):?(.*)', line_text)
            if java_exc_match and i + 1 < n and lines[i + 1].clean_text.strip().startswith("at "):
                start_line = lines[i].line_number
                exc_type = java_exc_match.group(1).strip()
                exc_msg = java_exc_match.group(2).strip()
                frame_lines = []
                j = i + 1
                while j < n:
                    curr = lines[j].clean_text.strip()
                    if curr.startswith("at ") or curr.startswith("... ") or curr.startswith("Caused by:"):
                        frame_lines.append(lines[j].clean_text)
                        j += 1
                    else:
                        break
                end_line = lines[j - 1].line_number
                raw_trace = "\n".join(lines[k].clean_text for k in range(i, j))
                traces.append(
                    StackTrace(
                        start_line=start_line,
                        end_line=end_line,
                        language="java",
                        exception_type=exc_type,
                        exception_message=exc_msg,
                        frames=frame_lines,
                        raw_text=raw_trace,
                    )
                )
                i = j
                continue

            # 3. JavaScript / Node.js
            # e.g.: TypeError: Cannot read property 'foo' of undefined
            #           at /app/server.js:42:15
            js_exc_match = re.match(r'^(TypeError|ReferenceError|SyntaxError|RangeError|Error|CustomError):\s*(.*)', line_text.strip())
            if js_exc_match and i + 1 < n and "    at " in lines[i + 1].clean_text:
                start_line = lines[i].line_number
                exc_type = js_exc_match.group(1).strip()
                exc_msg = js_exc_match.group(2).strip()
                frame_lines = []
                j = i + 1
                while j < n and "    at " in lines[j].clean_text:
                    frame_lines.append(lines[j].clean_text)
                    j += 1
                end_line = lines[j - 1].line_number
                raw_trace = "\n".join(lines[k].clean_text for k in range(i, j))
                traces.append(
                    StackTrace(
                        start_line=start_line,
                        end_line=end_line,
                        language="javascript",
                        exception_type=exc_type,
                        exception_message=exc_msg,
                        frames=frame_lines,
                        raw_text=raw_trace,
                    )
                )
                i = j
                continue

            # 4. Go Panic Trace
            if line_text.startswith("panic: "):
                start_line = lines[i].line_number
                exc_msg = line_text[7:].strip()
                exc_type = "panic"
                frame_lines = []
                j = i + 1
                while j < n and (lines[j].clean_text.startswith("goroutine ") or lines[j].clean_text.startswith("\t") or lines[j].clean_text.endswith(")")):
                    frame_lines.append(lines[j].clean_text)
                    j += 1
                end_line = lines[j - 1].line_number if j > i + 1 else start_line
                raw_trace = "\n".join(lines[k].clean_text for k in range(i, max(j, i + 1)))
                traces.append(
                    StackTrace(
                        start_line=start_line,
                        end_line=end_line,
                        language="go",
                        exception_type=exc_type,
                        exception_message=exc_msg,
                        frames=frame_lines,
                        raw_text=raw_trace,
                    )
                )
                i = j
                continue

            i += 1

        return traces

    def _cluster_error_groups(self, lines: List[ParsedLogLine]) -> List[ErrorGroup]:
        """Groups repeated errors by normalized message signature."""
        error_lines = [l for l in lines if l.is_error]
        clusters: Dict[str, Dict] = defaultdict(lambda: {
            "count": 0,
            "sample_message": "",
            "first_line": -1,
            "last_line": -1,
            "timestamps": []
        })

        for pl in error_lines:
            sig = self._normalize_signature(pl.clean_text)
            c = clusters[sig]
            c["count"] += 1
            if c["count"] == 1:
                c["sample_message"] = pl.clean_text.strip()
                c["first_line"] = pl.line_number
            c["last_line"] = pl.line_number
            if pl.timestamp:
                c["timestamps"].append(pl.timestamp)

        # Convert to list and sort by count descending
        groups = []
        for sig, data in clusters.items():
            groups.append(
                ErrorGroup(
                    signature=sig,
                    sample_message=data["sample_message"],
                    count=data["count"],
                    first_seen_line=data["first_line"],
                    last_seen_line=data["last_line"],
                    timestamps=data["timestamps"][:5],  # keep top 5
                )
            )

        groups.sort(key=lambda x: x.count, reverse=True)
        return groups

    def _normalize_signature(self, text: str) -> str:
        """Strips dynamic values to create a message template signature."""
        sig = text.strip()
        for pat, repl in NORMALIZE_RULES:
            sig = pat.sub(repl, sig)
        return sig[:250]  # truncate signature length

    def _build_timeline(self, lines: List[ParsedLogLine]) -> List[TimelinePoint]:
        """Aggregates log events over chronological minute buckets."""
        time_buckets: Dict[str, Dict[str, int]] = defaultdict(lambda: {"error": 0, "warn": 0, "info": 0})

        for pl in lines:
            if not pl.timestamp:
                continue

            # Normalize timestamp to minute bucket (YYYY-MM-DD HH:MM or similar)
            bucket_key = pl.timestamp[:16]  # usually covers YYYY-MM-DD HH:MM or Oct 18 10:15
            if pl.is_error:
                time_buckets[bucket_key]["error"] += 1
            elif pl.level in (LogLevel.WARN, LogLevel.WARNING):
                time_buckets[bucket_key]["warn"] += 1
            else:
                time_buckets[bucket_key]["info"] += 1

        points = []
        for bucket, counts in time_buckets.items():
            points.append(
                TimelinePoint(
                    timestamp=bucket,
                    error_count=counts["error"],
                    warning_count=counts["warn"],
                    info_count=counts["info"],
                )
            )

        return points
