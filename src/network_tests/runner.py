"""
Network Test Runner – orchestration layer for the Network Diagnostics Engine.

This module provides the central execution point for network diagnostic tests.
Its responsibilities are:

1. Accept a test type + target + parameters.
2. Dispatch to the appropriate low-level network primitive.
3. Wrap the result in the standardized :class:`TestResult` contract.
4. Handle unexpected programming errors separately from normal network failures.
5. Centralise consistent logging (test start, target, outcome, duration).

The runner does *not* implement ICMP/TCP/UDP/port logic itself.  Each primitive
remains an independent, reusable component in its own module.  This separation
keeps the architecture clean, testable, and extensible for future engines
(DNS, TLS, HTTP, performance, etc.) without modifying this file.

Example usage::

    runner = NetworkTestRunner()
    result = runner.run("tcp", "example.com:443", timeout=3.0)
    print(result.status, result.error)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from utils.logger import get_logger

from .results import TestResult
from .target import Target
from . import ping, tcp, port, udp  # noqa: F401  (re-exported)

logger = get_logger("network_tests.runner")


@dataclass
class TestConfig:
    """
    Lightweight runner-level configuration.

    This is the simplest configuration container that later phases (CLI,
    FastAPI, background jobs) can extend without changing the runner's core.
    """

    timeout: float = 3.0
    default_protocol: str = "tcp"
    log_level: str = "INFO"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestConfig":
        """Build a `TestConfig` from a plain dict (e.g. JSON payload)."""
        return cls(
            timeout=float(data.get("timeout", cls.timeout)),
            default_protocol=str(data.get("default_protocol", cls.default_protocol)),
            log_level=str(data.get("log_level", cls.log_level)),
        )


class NetworkTestRunner:
    """
    Central, consistent executor for network diagnostic tests.

    The runner is deliberately thin: it only orchestrates.  All low-level
    network logic lives in `ping`, `tcp`, `port`, `udp`.

    Supported test types:
        - "ping"        (ICMP)
        - "tcp"         (TCP connection)
        - "port"        (port availability)
        - "udp"         (UDP send / send-receive)


    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        test_type: str,
        target: str,
        **kwargs: Any,
    ) -> TestResult:
        """
        Execute a network diagnostic test and return a standardised result.

        Args:
            test_type: One of "ping", "tcp", "port", "udp".
            target: Target string (e.g. "example.com:443", "8.8.8.8", "192.168.1.10").
            **kwargs: Forwarded to the underlying test function as:
                - timeout (float): connection/socket timeout in seconds.
                  Defaults to `TestConfig.timeout`.
                - count (int):  only for "ping" – number of ICMP requests.
                - protocol (str): override protocol for "udp"/"tcp".

        Returns:
            A `TestResult` with standardised fields.

        Raises:
            ValueError: If `test_type` is not supported.
            TypeError: If `target` is not a string.
        """
        test_type = (test_type or "").strip().lower()
        if test_type not in self._TEST_DISPATCH:
            raise ValueError(
                f"Unsupported test type '{test_type}'. "
                f"Supported: {sorted(self._TEST_DISPATCH.keys())}"
            )

        if not isinstance(target, str):
            raise TypeError(f"target must be a string, got {type(target).__name__}")

        # Parse target into a clean Target object (centralised parsing)
        target_obj = Target.from_string(target)

        # Normalise per-test kwargs
        params = self._normalise_kwargs(test_type, kwargs)

        # Measure execution
        start = datetime.now(timezone.utc)

        # Execute the low-level test
        try:
            module_result = self._execute_test(test_type, target_obj, params)
        except Exception as exc:  # noqa: BLE001 - catch-all for unexpected errors
            # Programming-level errors (bug in runner, socket creation failure,
            # etc.) are NOT network-test failures.  They are raised so callers
            # can distinguish them from normal network failures.
            duration_ms = self._elapsed_ms(start)
            self._logger.error(
                f"Unexpected exception in '{test_type}' for '{target}': {exc!r}"
            )
            raise

        duration_ms = self._elapsed_ms(start)

        # Convert module result to standardised TestResult
        try:

    # ------------------------------------------------------------------
    # Per-type converters (module result -> standardised result)
    # ------------------------------------------------------------------

    def _convert_ping(
        self, module_result: Any, target_obj: Target, duration_ms: float
    ) -> TestResult:
        status = "PASS" if module_result.is_reachable else "FAIL"
        error = module_result.error_detail if status == "FAIL" else None
        metadata = {
            "is_reachable": module_result.is_reachable,
            "raw_output": module_result.raw_output,
            "message": module_result.message,
        }
        return TestResult(
            test_name="Ping",
            status=status,
            target=target_obj.to_string(),
            duration_ms=duration_ms,
            latency_ms=None,  # ICMP latency measured via system ping (not exposed)
            error=error,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata,
        )

    def _convert_tcp(
        self, module_result: Any, target_obj: Target, duration_ms: float
    ) -> TestResult:
        status = "PASS" if module_result.is_connected else "FAIL"
        error = module_result.error_type if status == "FAIL" else None
        metadata = {
            "is_connected": module_result.is_connected,
            "message": module_result.message,
            "error_type": module_result.error_type,
        }
        return TestResult(
            test_name="TCP Connectivity",
            status=status,
            target=target_obj.to_string(),
            duration_ms=duration_ms,
            latency_ms=None,
            error=error,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata,
        )

    def _convert_port(
        self, module_result: Any, target_obj: Target, duration_ms: float
    ) -> TestResult:
        status = "PASS" if module_result.is_open else "FAIL"
        error = module_result.error_detail if status == "FAIL" else None
        metadata = {
            "is_open": module_result.is_open,
            "state": module_result.state,
            "message": module_result.message,
            "error_detail": module_result.error_detail,
        }
        return TestResult(
            test_name="Port Check",
            status=status,
            target=target_obj.to_string(),
            duration_ms=duration_ms,
            latency_ms=None,
            error=error,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata,
        )

            standardized = self._to_standard_result(
                test_type, target_obj, module_result, duration_ms
            )
        except Exception as exc:  # noqa: BLE001
            # If conversion fails, fall back to a structured failure.
            self._logger.error(
                f"Failed to convert result for '{test_type}' "
                f"'{target_obj}': {exc!r}"
            )
            return TestResult.failure(
                test_name=test_type,
                target=target_obj.to_string(),
                message=f"Internal error formatting result: {exc!r}",
                duration_ms=duration_ms,
            )

        return standardized

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalise_kwargs(self, test_type: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalise per-test kwargs, filling defaults.
        """
        params = dict(kwargs)

        # Timeout default
        if "timeout" not in params:
            params["timeout"] = self.config.timeout

        # Per-test specific defaults
        if test_type == "ping" and "count" not in params:
            params["count"] = 1

        # Protocol default for tests that accept it
        if test_type in ("tcp", "udp", "port") and "protocol" not in params:
            params["protocol"] = self.config.default_protocol

        return params

    def _execute_test(
        self, test_type: str, target_obj: Target, params: Dict[str, Any]
    ) -> Any:
        """
        Call the low-level test function for the given test type.
        """
        module = self._TEST_DISPATCH[test_type]
        target_str = target_obj.to_string()

        # Build keyword args appropriate for this test type

    def _convert_udp(
        self, module_result: Any, target_obj: Target, duration_ms: float
    ) -> TestResult:
        status = "PASS" if module_result.success else "FAIL"
        error = module_result.error_type if status == "FAIL" else None
        metadata = {
            "success": module_result.success,
            "message": module_result.message,
            "sent": getattr(module_result, "sent", 0),
            "received": getattr(module_result, "received", 0),
            "latency_ms": module_result.latency_ms,
        }
        return TestResult(
            test_name="UDP Send",
            status=status,
            target=target_obj.to_string(),
            duration_ms=duration_ms,
            latency_ms=module_result.latency_ms,
            error=error,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Timing helper
    # ------------------------------------------------------------------

    @staticmethod
    def _elapsed_ms(start: datetime) -> float:
        """
        Compute elapsed time in milliseconds.

        Args:
            start: datetime captured at test start.

        Returns:
            Elapsed time in milliseconds, floored to 3 decimal places.
        """
        elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000.0
        return round(elapsed, 3)

        if test_type == "ping":
            return module.ping_target(
                host=target_obj.host,
                count=params.get("count", 1),
                timeout=params.get("timeout", self.config.timeout),
            )
        elif test_type == "tcp":
            return module.test_tcp_connection(
                host=target_obj.host,
                port=target_obj.port or 0,
                timeout=params.get("timeout", self.config.timeout),
            )
        elif test_type == "port":
            return module.check_port_availability(
                host=target_obj.host,
                port=target_obj.port or 0,
                timeout=params.get("timeout", self.config.timeout),
            )
        elif test_type == "udp":
            # UDP requires a port
            if target_obj.port is None:
                raise ValueError("UDP tests require a port in the target string.")
            return module.udp_send_receive(
                host=target_obj.host,
                port=target_obj.port,
                data=b"probe",
                timeout=params.get("timeout", self.config.timeout),
            )
        else:
            # Should never get here – already validated in run()
            raise ValueError(f"Unknown test type: {test_type}")

    Future engines (DNS, TLS, HTTP, performance, capacity) will be added as
    new modules and registered here without changing the dispatcher.
    """

    #: Mapping of test-type string -> low-level module that exposes the
    #: corresponding test function.
    _TEST_DISPATCH: Dict[str, Any] = {
        "ping": ping,
        "tcp": tcp,
        "port": port,
        "udp": udp,
    }

    def __init__(self, config: Optional[TestConfig] = None, logger: Any = None):
        """
        Initialise the runner.

        Args:
            config: Optional test configuration.  Uses defaults if `None`.
            logger: Optional logger instance.  Uses the module logger if `None`.
        """
        self.config = config or TestConfig()
        self._logger = logger or logger
