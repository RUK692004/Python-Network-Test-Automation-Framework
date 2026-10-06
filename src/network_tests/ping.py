"""
Ping connectivity test module for Network Test Automation Framework.

Executes system ping commands via subprocess, evaluates reachability,
and provides structured results and logging.
"""

import platform
import subprocess
from datetime import datetime, timezone
from typing import Optional

from utils.logger import get_logger

from .results import TestResult

logger = get_logger("network_tests.ping")


def _elapsed_ms(start: Optional[datetime]) -> float:
    """Elapsed milliseconds since ``start`` (0.0 when ``start`` is unset)."""
    if start is None:
        return 0.0
    return round((datetime.now(timezone.utc) - start).total_seconds() * 1000.0, 3)


def ping_target(
    host: str, timeout: int = 2, count: int = 1
) -> TestResult:
    """
    Perform an ICMP ping connectivity test against the specified target.

    Constructs and executes a platform-appropriate ping command via subprocess.

    Args:
        host: Target IP address or hostname.
        timeout: Timeout duration in seconds.
        count: Number of ICMP packet attempts (default: 1).

    Returns:
        TestResult: Structured test execution result.
    """
    logger.info(f"Starting Ping test for target: {host} (timeout={timeout}s, count={count})")

    if not host or not isinstance(host, str) or not host.strip():
        message = "Invalid target host provided."
        logger.error(f"Ping test FAILED: {message}")
        return TestResult.failure(
            test_name="Ping",
            target=str(host),
            message=message,
            duration_ms=0.0,
        )

    clean_host = host.strip()

    system_os = platform.system().lower()

    # Determine command flags based on OS
    if system_os == "windows":
        # Windows ping: -n count, -w timeout_in_milliseconds
        timeout_ms = int(timeout * 1000)
        cmd = ["ping", "-n", str(count), "-w", str(timeout_ms), clean_host]
    else:
        # Linux / WSL / macOS ping: -c count, -W timeout_in_seconds
        cmd = ["ping", "-c", str(count), "-W", str(timeout), clean_host]

    start = None
    try:
        start = datetime.now(timezone.utc)
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout + 2,  # Subprocess execution ceiling
        )
        elapsed_ms = _elapsed_ms(start)

        stdout = process.stdout or ""
        stderr = process.stderr or ""

        if process.returncode == 0:
            latency_ms = _parse_ping_latency(stdout)
            message = "Host is reachable"
            logger.info(f"Ping test PASSED: Target={clean_host} | Result: PASS | Message: {message}")
            return TestResult.success(
                test_name="Ping",
                target=clean_host,
                latency_ms=latency_ms,
                metadata={
                    "is_reachable": True,
                    "raw_output": stdout,
                    "packets_sent": _parse_packets_sent(stdout),
                    "packets_received": _parse_packets_received(stdout),
                    "packets_lost": _parse_packets_lost(stdout),
                    "packet_loss_percent": _parse_packet_loss_percent(stdout),
                },
                duration_ms=elapsed_ms,
            )
        else:
            message = "Host is unreachable"
            logger.warning(
                f"Ping test FAILED: Target={clean_host} | Result: FAIL | ReturnCode={process.returncode} | Message: {message}"
            )
            return TestResult.failure(
                test_name="Ping",
                target=clean_host,
                message=message,
                latency_ms=None,
                metadata={
                    "is_reachable": False,
                    "raw_output": stdout,
                    "packets_sent": _parse_packets_sent(stdout),
                    "packets_received": _parse_packets_received(stdout),
                    "packets_lost": _parse_packets_lost(stdout),
                    "packet_loss_percent": _parse_packet_loss_percent(stdout),
                },
                duration_ms=elapsed_ms,
            )

    except subprocess.TimeoutExpired:
        elapsed_ms = _elapsed_ms(start)
        message = f"Ping request timed out after {timeout} seconds"
        logger.error(f"Ping test FAILED: Target={clean_host} | Result: FAIL | Message: {message}")
        return TestResult.failure(
            test_name="Ping",
            target=clean_host,
            message=message,
            latency_ms=None,
            duration_ms=elapsed_ms,
        )
    except FileNotFoundError:
        elapsed_ms = _elapsed_ms(start)
        message = "Ping command utility not found on host system"
        logger.error(f"Ping test FAILED: Target={clean_host} | Result: FAIL | Message: {message}")
        return TestResult.failure(
            test_name="Ping",
            target=clean_host,
            message=message,
            latency_ms=None,
            duration_ms=elapsed_ms,
        )
    except OSError as err:
        elapsed_ms = _elapsed_ms(start)
        message = f"Operating system error during ping execution: {err}"
        logger.error(f"Ping test FAILED: Target={clean_host} | Result: FAIL | Exception: {err}")
        return TestResult.failure(
            test_name="Ping",
            target=clean_host,
            message=message,
            latency_ms=None,
            duration_ms=elapsed_ms,
        )






def _parse_ping_latency(stdout: str) -> Optional[float]:
    """
    Extract the minimum round-trip latency in milliseconds from ping output.

    Returns the minimum latency value, or None if the value cannot be parsed.
    """
    try:
        if platform.system().lower() == "windows":
            # Windows output: "Minimum = 1ms, Maximum = 2ms, Average = 1ms"
            match = __import__("re").search(r"Minimum\s*=\s*([\d.]+)\s*ms", stdout, __import__("re").IGNORECASE)
            if match:
                return float(match.group(1))
        else:
            # Linux/macOS output: "rtt min/avg/max/mdev = 0.012/0.015/0.018/0.003 ms"
            match = __import__("re").search(r"rtt min/avg/max/mdev\s*=\s*([\d.]+)/([\d.]+)/([\d.]+)/[\\d.]+ ms", stdout)
            if match:
                return float(match.group(1))
    except (ValueError, AttributeError):
        pass
    return None


def _parse_packets_sent(stdout: str) -> int:
    """Extract the number of packets sent from ping output."""
    try:
        if platform.system().lower() == "windows":
            match = __import__("re").search(r"Packets:\s*sent\s*=\s*(\d+)", stdout, __import__("re").IGNORECASE)
            if match:
                return int(match.group(1))
        else:
            match = __import__("re").search(r"(\d+)\s+packets?\s+sent", stdout, __import__("re").IGNORECASE)
            if match:
                return int(match.group(1))
    except (ValueError, AttributeError):
        pass
    return 0


def _parse_packets_received(stdout: str) -> int:
    """Extract the number of packets received from ping output."""
    try:
        if platform.system().lower() == "windows":
            match = __import__("re").search(r"Packets:\s*received\s*=\s*(\d+)", stdout, __import__("re").IGNORECASE)
            if match:
                return int(match.group(1))
        else:
            match = __import__("re").search(r"(\d+)\s+packets?\s+received", stdout, __import__("re").IGNORECASE)
            if match:
                return int(match.group(1))
    except (ValueError, AttributeError):
        pass
    return 0


def _parse_packets_lost(stdout: str) -> int:
    """Extract the number of packets lost from ping output."""
    try:
        if platform.system().lower() == "windows":
            match = __import__("re").search(r"Packets:\s*lost\s*=\s*(\d+)", stdout, __import__("re").IGNORECASE)
            if match:
                return int(match.group(1))
        else:
            match = __import__("re").search(r"(\d+)\s+packets?\s+lost", stdout, __import__("re").IGNORECASE)
            if match:
                return int(match.group(1))
    except (ValueError, AttributeError):
        pass
    return 0


def _parse_packet_loss_percent(stdout: str) -> float:
    """Extract the packet loss percentage from ping output."""
    try:
        if platform.system().lower() == "windows":
            match = __import__("re").search(r"Packets:\s*sent\s*=\s*\d+\s*,\s*received\s*=\s*\d+\s*,\s*lost\s*=\s*\d+\s*\((\d+(?:\.\d+)?)\s*%", stdout, __import__("re").IGNORECASE)
            if match:
                return float(match.group(1))
        else:
            match = __import__("re").search(r"loss\s*=\s*([\d.]+)\s*%", stdout, __import__("re").IGNORECASE)
            if match:
                return float(match.group(1))
    except (ValueError, AttributeError):
        pass
    return 0.0




