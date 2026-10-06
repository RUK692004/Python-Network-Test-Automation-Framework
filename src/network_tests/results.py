"""
Standardized test result model for the Network Diagnostics Engine.

This module defines the common result contract shared by all network tests
so that the framework can produce consistent, serializable results regardless
of the underlying test implementation (ICMP, TCP, UDP, port check).

The model is designed to be:
- Easy to serialize (plain dataclass + to_dict/by_dict helpers)
- Easy to test (no side effects, no network calls)
- Extensible (metadata dict absorbs test-specific fields)
- Suitable for future FastAPI/reporting integrations
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class TestResult:
    """
    Standardized result contract for a network diagnostic test.

    Attributes:
        test_name: Human-readable name of the test (e.g. "Ping", "TCP Connection").
            Consistent naming helps downstream consumers (API, reports, dashboards)
            group results by test type.
        status: Result outcome. At minimum supports "PASS" and "FAIL".  Future
            extensions such as "TIMEOUT", "SKIPPED", or "ERROR" may be added
            later; new statuses must be documented in the module docstring.
        target: Target identifier as a single string (e.g. "example.com:443",
            "192.168.1.10", or "8.8.8.8").  Target parsing/parsing logic is
            isolated in :mod:`network_tests.target` so this field stays stable.
        duration_ms: Wall-clock time the test took to execute, in milliseconds.
            This deliberately excludes any wrapper overhead beyond the test call.
        latency_ms: Network latency in milliseconds (round-trip for ICMP, accept
            handshake time for TCP, send/receive round-trip for UDP).  `null`/
            `None` when the metric is not applicable or not measurable for the
            specific test.
        error: Human-readable error message, or `null`/`None` on success.
            Normal network failures (connection refused, DNS failure, timeout)
            are surfaced here rather than raising – they become status="FAIL".
        timestamp: ISO-8601 UTC timestamp of test completion.
        metadata: Free-form dict for test-specific information that does not
            fit the common fields (e.g. ICMP packet loss, TCP error_type,
            port state).  Downstream components should not assume a known set
            of keys here.
    """

    test_name: str
    status: str
    target: str
    duration_ms: float
    latency_ms: Optional[float]
    error: Optional[str]
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------------------------
    # Status constants (documented for future extensibility).
    # ---------------------------------------------------------------------------
    STATUS_PASS = "PASS"
    STATUS_FAIL = "FAIL"
    STATUS_TIMEOUT = "TIMEOUT"
    STATUS_SKIPPED = "SKIPPED"
    STATUS_ERROR = "ERROR"

    @classmethod
    def success(
        cls,
        test_name: str,
        target: str,
        latency_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "TestResult":
        """Build a `TestResult` with status `STATUS_PASS`."""
        return cls(
            test_name=test_name,
            status=cls.STATUS_PASS,
            target=target,
            duration_ms=0.0,
            latency_ms=latency_ms,
            error=None,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        test_name: str,
        target: str,
        message: str,
        latency_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "TestResult":
        """Build a `TestResult` with status `STATUS_FAIL` and the given error."""
        return cls(
            test_name=test_name,
            status=cls.STATUS_FAIL,
            target=target,
            duration_ms=0.0,
            latency_ms=latency_ms,
            error=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

    @property
    def is_success(self) -> bool:
        """Return ``True`` when the result status is ``STATUS_PASS``."""
        return self.status == self.STATUS_PASS

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict representation of the result."""
        data = asdict(self)
        # Normalize timestamp (already ISO format, but ensure it is plain str)
        data["timestamp"] = str(data["timestamp"])
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestResult":
        """Construct a `TestResult` from a JSON-serializable dict."""
        return cls(
            test_name=str(data["test_name"]),
            status=str(data["status"]),
            target=str(data["target"]),
            duration_ms=float(data["duration_ms"]),
            latency_ms=cls._as_optional_float(data.get("latency_ms")),
            error=cls._as_optional_str(data.get("error")),
            timestamp=str(data["timestamp"]),
            metadata=dict(data.get("metadata", {}) or {}),
        )

    @staticmethod
    def _as_optional_float(value: Any) -> Optional[float]:
        if value is None or isinstance(value, (str, bytes)) and not value.strip():
            return None
        return float(value)

    @staticmethod
    def _as_optional_str(value: Any) -> Optional[str]:
        if value is None or (isinstance(value, (str, bytes)) and not value.strip()):
            return None
        return str(value)
