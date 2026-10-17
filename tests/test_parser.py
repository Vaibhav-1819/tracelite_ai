"""
Tests for LogParser
"""

import os
import pytest
from tracelite.parser import LogParser


def test_empty_log():
    parser = LogParser()
    analysis = parser.parse("")
    assert analysis.total_lines == 0
    assert analysis.error_count == 0
    assert len(analysis.stack_traces) == 0


def test_python_zerodivision_fixture():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "python_zero_division.log")
    with open(fixture_path, "r", encoding="utf-8") as f:
        content = f.read()

    parser = LogParser()
    analysis = parser.parse(content)

    assert analysis.total_lines > 5
    assert analysis.error_count >= 1
    assert len(analysis.stack_traces) == 1

    trace = analysis.stack_traces[0]
    assert trace.language == "python"
    assert trace.exception_type == "ZeroDivisionError"
    assert "division by zero" in trace.exception_message
    assert len(trace.frames) >= 2
    assert analysis.primary_error == "ZeroDivisionError: division by zero"

    # Secret masking should have caught the fake sk- token in the log
    assert analysis.masked_secrets_count >= 1


def test_java_nullpointer_fixture():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "java_null_pointer.log")
    with open(fixture_path, "r", encoding="utf-8") as f:
        content = f.read()

    parser = LogParser()
    analysis = parser.parse(content)

    assert analysis.total_lines > 5
    assert len(analysis.stack_traces) == 1
    trace = analysis.stack_traces[0]
    assert trace.language == "java"
    assert "NullPointerException" in trace.exception_type
    assert len(trace.frames) >= 3


def test_http_server_errors_fixture():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "http_server_errors.log")
    with open(fixture_path, "r", encoding="utf-8") as f:
        content = f.read()

    parser = LogParser()
    analysis = parser.parse(content)

    assert analysis.error_count >= 5
    # Should have grouped repeated checkout 500s and repeated 429 rate limits
    assert len(analysis.error_groups) >= 2

    # Group counts check
    top_group = analysis.error_groups[0]
    assert top_group.count >= 4

    # Timeline buckets
    assert len(analysis.timeline) >= 2
