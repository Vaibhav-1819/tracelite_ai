"""
TraceLite AI - Data Models
Defines structured classes for logs, stack traces, groupings, and investigation reports.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class LogLevel(str, Enum):
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"
    ERROR = "ERROR"
    WARN = "WARN"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_string(cls, val: str) -> "LogLevel":
        val_upper = val.upper()
        for level in cls:
            if level.value == val_upper:
                return level
        if val_upper in ("ERR", "STDERR"):
            return cls.ERROR
        if val_upper in ("WRN",):
            return cls.WARNING
        return cls.UNKNOWN


@dataclass
class ParsedLogLine:
    line_number: int
    raw_text: str
    clean_text: str
    timestamp: Optional[str] = None
    level: LogLevel = LogLevel.UNKNOWN
    message: str = ""
    is_error: bool = False


@dataclass
class StackTrace:
    start_line: int
    end_line: int
    language: str  # python, java, javascript, go, generic
    exception_type: str
    exception_message: str
    frames: List[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class ErrorGroup:
    signature: str
    sample_message: str
    count: int
    first_seen_line: int
    last_seen_line: int
    timestamps: List[str] = field(default_factory=list)


@dataclass
class TimelinePoint:
    timestamp: str
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0


@dataclass
class DeterministicAnalysis:
    total_lines: int
    error_count: int
    warning_count: int
    stack_traces: List[StackTrace] = field(default_factory=list)
    error_groups: List[ErrorGroup] = field(default_factory=list)
    timeline: List[TimelinePoint] = field(default_factory=list)
    primary_error: Optional[str] = None
    masked_secrets_count: int = 0


@dataclass
class AIHypothesis:
    title: str
    explanation: str
    likely_causes: List[str] = field(default_factory=list)
    suggested_steps: List[str] = field(default_factory=list)
    confidence_statement: str = ""
    model_name: str = "qwen2.5:0.5b"
    is_fallback: bool = False
    evidence_referenced: List[str] = field(default_factory=list)


@dataclass
class InvestigationReport:
    report_id: str
    generated_at: str
    analysis: DeterministicAnalysis
    hypothesis: AIHypothesis
    raw_log_sample: str = ""
