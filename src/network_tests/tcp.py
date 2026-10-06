"""
TCP connectivity test module for Network Test Automation Framework.

Attempts TCP socket connections to target hosts and ports using Python socket module,
ensuring sockets are safely closed and all network exceptions are handled cleanly.
"""

import socket
import time

from utils.logger import get_logger

from .results import TestResult

logger = get_logger("network_tests.tcp")


def test_tcp_connection(
    host: str, port: int, timeout: float = 3.0
) -> TestResult:
    """
    Test TCP socket connectivity to a specified target host and port.

    Args:
        host: Target IP address or hostname.
        port: Target TCP port number.
        timeout: Socket connection timeout in seconds.

    Returns:
        TestResult: Canonical result.  ``metadata`` carries ``is_connected``,
        ``message``, ``error_type`` and ``port``; ``latency_ms`` holds the
        measured TCP handshake time on success.
    """
    logger.info(f"Starting TCP connection test for target {host}:{port} (timeout={timeout}s)")

    if not host or not isinstance(host, str) or not host.strip():
        msg = "Invalid target host provided"
        logger.error(f"TCP test FAILED: {msg}")
        return TestResult.failure(
            test_name="TCP Connectivity",
            target=f"{host}:{port}",
            message=msg,
            metadata={
                "is_connected": False,
                "message": msg,
                "error_type": "ValueError",
                "port": port,
            },
        )

    if not isinstance(port, int) or not (1 <= port <= 65535):
        msg = f"Invalid port number: {port}. Port must be between 1 and 65535."
        logger.error(f"TCP test FAILED: {msg}")
        return TestResult.failure(
            test_name="TCP Connectivity",
            target=f"{host}:{port}",
            message=msg,
            metadata={
                "is_connected": False,
                "message": msg,
                "error_type": "ValueError",
                "port": port,
            },
        )

    clean_host = host.strip()

    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        logger.info(f"Connecting to {clean_host}:{port}...")
        start = time.perf_counter()
        sock.connect((clean_host, port))
        latency_ms = round((time.perf_counter() - start) * 1000.0, 3)

        message = "TCP connection established"
        logger.info(f"TCP CONNECTION TEST | Target: {clean_host}:{port} | Result: PASS | Message: {message}")
        return TestResult.success(
            test_name="TCP Connectivity",
            target=f"{clean_host}:{port}",
            latency_ms=latency_ms,
            duration_ms=latency_ms,
            metadata={
                "is_connected": True,
                "message": message,
                "error_type": None,
                "port": port,
            },
        )

    except socket.timeout:
        message = f"Connection timed out after {timeout} seconds"
        logger.error(f"TCP CONNECTION TEST FAILED | Target: {clean_host}:{port} | Result: FAIL | Message: {message}")
        return TestResult.failure(
            test_name="TCP Connectivity",
            target=f"{clean_host}:{port}",
            message=message,
            metadata={
                "is_connected": False,
                "message": message,
                "error_type": "socket.timeout",
                "port": port,
            },
        )

    except ConnectionRefusedError:
        message = "Connection refused"
        logger.error(f"TCP CONNECTION TEST FAILED | Target: {clean_host}:{port} | Result: FAIL | Message: {message}")
        return TestResult.failure(
            test_name="TCP Connectivity",
            target=f"{clean_host}:{port}",
            message=message,
            metadata={
                "is_connected": False,
                "message": message,
                "error_type": "ConnectionRefusedError",
                "port": port,
            },
        )

    except socket.gaierror as err:
        message = f"DNS resolution failed for hostname '{clean_host}'"
        logger.error(
            f"TCP CONNECTION TEST FAILED | Target: {clean_host}:{port} | Result: FAIL | Message: {message} ({err})"
        )
        return TestResult.failure(
            test_name="TCP Connectivity",
            target=f"{clean_host}:{port}",
            message=message,
            metadata={
                "is_connected": False,
                "message": message,
                "error_type": "socket.gaierror",
                "port": port,
            },
        )

    except OSError as err:
        message = f"Network socket error: {err}"
        logger.error(
            f"TCP CONNECTION TEST FAILED | Target: {clean_host}:{port} | Result: FAIL | Message: {message}"
        )
        return TestResult.failure(
            test_name="TCP Connectivity",
            target=f"{clean_host}:{port}",
            message=message,
            metadata={
                "is_connected": False,
                "message": message,
                "error_type": "OSError",
                "port": port,
            },
        )

    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
