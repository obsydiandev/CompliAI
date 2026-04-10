"""Test-report parser — parse CSV and JSON test result files into structured dicts.

Supports:
- Generic CSV: columns detected automatically (test_name, status/result, score, etc.)
- JUnit-style XML (basic, no lxml dependency — stdlib xml.etree only)
- JSON flat list: ``[{"name": "...", "status": "pass", ...}, ...]``
- JSON summary dict: ``{"total": 10, "passed": 8, "failed": 2, "metrics": {...}}``
"""

from __future__ import annotations

import csv
import io
import json
import logging
import xml.etree.ElementTree as ET
from typing import Any

logger = logging.getLogger(__name__)


class ParsedReport:
    """Structured result of a parsed test report."""

    def __init__(
        self,
        format: str,
        total: int,
        passed: int,
        failed: int,
        skipped: int,
        test_cases: list[dict[str, Any]],
        metrics: dict[str, Any],
        raw_summary: str,
    ) -> None:
        self.format = format
        self.total = total
        self.passed = passed
        self.failed = failed
        self.skipped = skipped
        self.test_cases = test_cases
        self.metrics = metrics
        self.raw_summary = raw_summary

    def pass_rate(self) -> float | None:
        if self.total > 0:
            return round(self.passed / self.total, 4)
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "pass_rate": self.pass_rate(),
            "test_cases": self.test_cases[:50],  # cap for storage
            "metrics": self.metrics,
            "raw_summary": self.raw_summary,
        }

    def to_annex_iv_section4(self) -> dict[str, Any]:
        """Return a partial Section 4 content dict from the parsed report."""
        lines = [f"Test results ({self.format} format):"]
        lines.append(f"  Total: {self.total}, Passed: {self.passed}, Failed: {self.failed}")
        if self.pass_rate() is not None:
            lines.append(f"  Pass rate: {self.pass_rate():.1%}")
        if self.metrics:
            lines.append("  Metrics:")
            for k, v in list(self.metrics.items())[:10]:
                lines.append(f"    {k}: {v}")
        content: dict[str, Any] = {
            "test_metrics": "\n".join(lines),
        }
        return content


def parse_report(content: bytes, filename: str) -> ParsedReport:
    """Detect file format and parse the report.

    Args:
        content: Raw file bytes.
        filename: Original filename (used for extension hint).

    Returns:
        ParsedReport instance.
    """
    fname = filename.lower()
    if fname.endswith(".xml"):
        return _parse_xml(content)
    if fname.endswith(".csv"):
        return _parse_csv(content)
    # Try JSON regardless of extension
    try:
        return _parse_json(content)
    except (json.JSONDecodeError, ValueError):
        pass
    # Fall back to CSV
    try:
        return _parse_csv(content)
    except Exception:
        pass
    # Last resort: treat as plain text summary
    return ParsedReport(
        format="text",
        total=0,
        passed=0,
        failed=0,
        skipped=0,
        test_cases=[],
        metrics={},
        raw_summary=content.decode("utf-8", errors="replace")[:2000],
    )


def _parse_csv(content: bytes) -> ParsedReport:
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise ValueError("Empty CSV")

    # Normalise column names
    def _col(row: dict, *candidates: str) -> str | None:
        for c in candidates:
            for k in row:
                if k.strip().lower() == c:
                    return row[k]
        return None

    test_cases = []
    passed = failed = skipped = 0
    for row in rows:
        name = _col(row, "name", "test", "test_name", "testname") or list(row.values())[0]
        status_raw = (
            (_col(row, "status", "result", "outcome", "passed", "state") or "").strip().lower()
        )
        if status_raw in ("pass", "passed", "ok", "true", "1", "success"):
            status = "pass"
            passed += 1
        elif status_raw in ("skip", "skipped", "xfail", "ignore"):
            status = "skip"
            skipped += 1
        else:
            status = "fail"
            failed += 1
        test_cases.append({"name": name, "status": status})

    total = len(rows)
    return ParsedReport(
        format="csv",
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        test_cases=test_cases,
        metrics={},
        raw_summary=f"{total} rows parsed from CSV",
    )


def _parse_json(content: bytes) -> ParsedReport:
    data = json.loads(content)
    if isinstance(data, list):
        return _parse_json_list(data)
    if isinstance(data, dict):
        return _parse_json_dict(data)
    raise ValueError("Unsupported JSON structure")


def _parse_json_list(rows: list) -> ParsedReport:
    test_cases = []
    passed = failed = skipped = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = row.get("name") or row.get("test_name") or row.get("id") or "unknown"
        status_raw = str(
            row.get("status") or row.get("result") or row.get("outcome") or "fail"
        ).lower()
        if status_raw in ("pass", "passed", "ok", "true", "1", "success"):
            status = "pass"
            passed += 1
        elif status_raw in ("skip", "skipped"):
            status = "skip"
            skipped += 1
        else:
            status = "fail"
            failed += 1
        test_cases.append({"name": name, "status": status})

    total = len(test_cases)
    return ParsedReport(
        format="json_list",
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        test_cases=test_cases,
        metrics={},
        raw_summary=f"{total} tests from JSON array",
    )


def _parse_json_dict(data: dict) -> ParsedReport:
    total = int(data.get("total", 0) or data.get("tests", 0))
    passed = int(data.get("passed", 0) or data.get("success", 0))
    failed = int(data.get("failed", 0) or data.get("failures", 0) or data.get("errors", 0))
    skipped = int(data.get("skipped", 0))
    if not total:
        total = passed + failed + skipped
    metrics = data.get("metrics") or data.get("summary") or {}
    if not isinstance(metrics, dict):
        metrics = {}
    return ParsedReport(
        format="json_dict",
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        test_cases=[],
        metrics=metrics,
        raw_summary=f"total={total} pass={passed} fail={failed}",
    )


def _parse_xml(content: bytes) -> ParsedReport:
    root = ET.fromstring(content.decode("utf-8", errors="replace"))
    # JUnit format: <testsuite> or <testsuites>
    suites = root.findall(".//testsuite") or ([root] if root.tag == "testsuite" else [])
    test_cases = []
    total = passed = failed = skipped = 0
    for suite in suites:
        for tc in suite.findall("testcase"):
            name = tc.get("name") or "unknown"
            if tc.find("failure") is not None or tc.find("error") is not None:
                status = "fail"
                failed += 1
            elif tc.find("skipped") is not None:
                status = "skip"
                skipped += 1
            else:
                status = "pass"
                passed += 1
            total += 1
            test_cases.append({"name": name, "status": status})

    if not total and root.get("tests"):
        total = int(root.get("tests", 0))
        failures = int(root.get("failures", 0))
        errors = int(root.get("errors", 0))
        skipped_attr = int(root.get("skipped", 0))
        failed = failures + errors
        skipped = skipped_attr
        passed = total - failed - skipped

    return ParsedReport(
        format="junit_xml",
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        test_cases=test_cases,
        metrics={},
        raw_summary=f"JUnit XML: {total} tests, {passed} passed, {failed} failed",
    )
