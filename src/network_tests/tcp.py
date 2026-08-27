"""
TCP connectivity test module for Network Test Automation Framework.

Attempts TCP socket connections to target hosts and ports using Python socket module,
ensuring sockets are safely closed and all network exceptions are handled cleanly.
"""

from dataclasses import dataclass
import socket
from typing import Optional

from utils.logger import get_logger

logger = get_logger("network_tests.tcp")


@dataclass
class TCPResult:
    """
    Data class representing the outcome of a TCP connection test.

    Attributes:
        target: Target hostname or IP address.
        port: Target TCP port.
        is_connected: True if TCP handshake completed successfully.
        status: PASS or FAIL string status.
        message: Human-readable status or failure explanation.
        error_type: Name of exception encountered if failed (e.g. ConnectionRefusedError).
    """

    target: str
    port: int
    is_connected: bool
    status: str
    message: str
    error_type: Optional[str] = None


def test_tcp_connection(
    host: str, port: int, timeout: float = 3.0
) -> TCPResult:
    """
    Test TCP socket connectivity to a specified target host and port.

    Args:
        host: Target IP address or hostname.
        port: Target TCP port number.
        timeout: Socket connection timeout in seconds.

    Returns:
        TCPResult: Structured result of the TCP connection attempt.
    """
    logger.info(f"Starting TCP connection test for target {host}:{port} (timeout={timeout}s)")

    if not host or not isinstance(host, str) or not host.strip():
        msg = "Invalid target host provided"
        logger.error(f"TCP test FAILED: {msg}")
        return TCPResult(
            target=str(host),
            port=port,
            is_connected=False,
            status="FAIL",
            message=msg,
            error_type="ValueError",
        )

    if not isinstance(port, int) or not (1 <= port <= 65535):
        msg = f"Invalid port number: {port}. Port must be between 1 and 65535."
        logger.error(f"TCP test FAILED: {msg}")
        return TCPResult(
            target=host,
            port=port,
            is_connected=False,
            status="FAIL",
            message=msg,
            error_type="ValueError",
        )

    clean_host = host.strip()

    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        logger.info(f"Connecting to {clean_host}:{port}...")
        sock.connect((clean_host, port))

        message = "TCP connection established"
        logger.info(f"TCP CONNECTION TEST | Target: {clean_host}:{port} | Result: PASS | Message: {message}")
        return TCPResult(
            target=clean_host,
            port=port,
            is_connected=True,
            status="PASS",
            message=message,
        )

    except socket.timeout:
        message = f"Connection timed out after {timeout} seconds"
        logger.error(f"TCP CONNECTION TEST FAILED | Target: {clean_host}:{port} | Result: FAIL | Message: {message}")
        return TCPResult(
            target=clean_host,
            port=port,
            is_connected=False,
            status="FAIL",
            message=message,
            error_type="socket.timeout",
        )

    except ConnectionRefusedError:
        message = "Connection refused"
        logger.error(f"TCP CONNECTION TEST FAILED | Target: {clean_host}:{port} | Result: FAIL | Message: {message}")
        return TCPResult(
            target=clean_host,
            port=port,
            is_connected=False,
            status="FAIL",
            message=message,
            error_type="ConnectionRefusedError",
        )

    except socket.gaierror as err:
        message = f"DNS resolution failed for hostname '{clean_host}'"
        logger.error(
            f"TCP CONNECTION TEST FAILED | Target: {clean_host}:{port} | Result: FAIL | Message: {message} ({err})"
        )
        return TCPResult(
            target=clean_host,
            port=port,
            is_connected=False,
            status="FAIL",
            message=message,
            error_type="socket.gaierror",
        )

    except OSError as err:
        message = f"Network socket error: {err}"
        logger.error(
            f"TCP CONNECTION TEST FAILED | Target: {clean_host}:{port} | Result: FAIL | Message: {message}"
        )
        return TCPResult(
            target=clean_host,
            port=port,
            is_connected=False,
            status="FAIL",
            message=message,
            error_type="OSError",
        )

    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
