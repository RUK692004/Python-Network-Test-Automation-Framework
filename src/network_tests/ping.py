"""
Ping connectivity test module for Network Test Automation Framework.

Executes system ping commands via subprocess, evaluates reachability,
and provides structured results and logging.
"""

from dataclasses import dataclass
import platform
import subprocess
from typing import Optional

from utils.logger import get_logger

logger = get_logger("network_tests.ping")


@dataclass
class PingResult:
    """
    Data class representing the result of a ping connectivity test.

    Attributes:
        target: IP address or hostname tested.
        is_reachable: True if the target responded to ICMP echo requests.
        status: PASS or FAIL string representation.
        message: Descriptive summary of the test outcome.
        raw_output: Standard output captured from the ping command.
        error_detail: Error details or stderr output if failure occurred.
    """

    target: str
    is_reachable: bool
    status: str
    message: str
    raw_output: str = ""
    error_detail: Optional[str] = None


def ping_target(
    host: str, timeout: int = 2, count: int = 1
) -> PingResult:
    """
    Perform an ICMP ping connectivity test against the specified target.

    Constructs and executes a platform-appropriate ping command via subprocess.

    Args:
        host: Target IP address or hostname.
        timeout: Timeout duration in seconds.
        count: Number of ICMP packet attempts (default: 1).

    Returns:
        PingResult: Structured test execution result.
    """
    logger.info(f"Starting Ping test for target: {host} (timeout={timeout}s, count={count})")

    if not host or not isinstance(host, str) or not host.strip():
        message = "Invalid target host provided."
        logger.error(f"Ping test FAILED: {message}")
        return PingResult(
            target=str(host),
            is_reachable=False,
            status="FAIL",
            message=message,
            error_detail=message,
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

    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout + 2,  # Subprocess execution ceiling
        )

        stdout = process.stdout or ""
        stderr = process.stderr or ""

        if process.returncode == 0:
            message = "Host is reachable"
            logger.info(f"Ping test PASSED: Target={clean_host} | Result: PASS | Message: {message}")
            return PingResult(
                target=clean_host,
                is_reachable=True,
                status="PASS",
                message=message,
                raw_output=stdout,
            )
        else:
            message = "Host is unreachable"
            logger.warning(
                f"Ping test FAILED: Target={clean_host} | Result: FAIL | ReturnCode={process.returncode} | Message: {message}"
            )
            return PingResult(
                target=clean_host,
                is_reachable=False,
                status="FAIL",
                message=message,
                raw_output=stdout,
                error_detail=stderr or stdout,
            )

    except subprocess.TimeoutExpired:
        message = f"Ping request timed out after {timeout} seconds"
        logger.error(f"Ping test FAILED: Target={clean_host} | Result: FAIL | Message: {message}")
        return PingResult(
            target=clean_host,
            is_reachable=False,
            status="FAIL",
            message=message,
            error_detail=message,
        )
    except FileNotFoundError:
        message = "Ping command utility not found on host system"
        logger.error(f"Ping test FAILED: Target={clean_host} | Result: FAIL | Message: {message}")
        return PingResult(
            target=clean_host,
            is_reachable=False,
            status="FAIL",
            message=message,
            error_detail=message,
        )
    except OSError as err:
        message = f"Operating system error during ping execution: {err}"
        logger.error(f"Ping test FAILED: Target={clean_host} | Result: FAIL | Exception: {err}")
        return PingResult(
            target=clean_host,
            is_reachable=False,
            status="FAIL",
            message=message,
            error_detail=str(err),
        )
