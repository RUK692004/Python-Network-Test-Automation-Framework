"""
UDP networking module for Network Test Automation Framework.

Provides reusable UDP socket operations: sending datagrams, sending and
receiving a response (with latency measurement), input validation, and
explicit handling of socket errors and timeouts. All sockets are closed
safely via try/finally.
"""

from dataclasses import dataclass
import socket
import time
from typing import Optional

from utils.logger import get_logger

logger = get_logger("network_tests.udp")

DEFAULT_BUFFER_SIZE = 4096
PORT_MIN = 1
PORT_MAX = 65535


@dataclass
class UDPResult:
    """
    Structured result of a single UDP operation.

    Attributes:
        success: True if the operation completed as intended.
        host: Target IP address or hostname.
        port: Target UDP port.
        message: Human-readable summary of the outcome.
        latency_ms: Round-trip time in milliseconds (only for send/receive).
        error_type: Name of the exception/condition if the operation failed.
        sent: Number of datagrams sent.
        received: Number of responses received.
    """

    success: bool
    host: str
    port: int
    message: str
    latency_ms: Optional[float] = None
    error_type: Optional[str] = None
    sent: int = 1
    received: int = 0

    def __str__(self) -> str:
        return (
            f"UDPResult(success={self.success}, host={self.host}, port={self.port}, "
            f"message={self.message!r}, latency_ms={self.latency_ms}, "
            f"error_type={self.error_type})"
        )


def _validate_target(host: str, port: int) -> Optional[str]:
    """
    Validate a UDP target (host and port).

    Args:
        host: Target IP address or hostname.
        port: Target UDP port number.

    Returns:
        An error message string if the target is invalid, otherwise None.
    """
    if not isinstance(host, str) or not host.strip():
        return "Invalid target host provided"
    if not isinstance(port, int) or not (PORT_MIN <= port <= PORT_MAX):
        return (
            f"Invalid port number: {port}. Port must be between {PORT_MIN} and {PORT_MAX}."
        )
    return None


def _validate_udp_options(data: bytes, timeout: float) -> Optional[str]:
    """
    Validate UDP operation options (payload type and positive timeout).

    Args:
        data: Payload bytes to transmit.
        timeout: Socket timeout in seconds.

    Returns:
        An error message string if the options are invalid, otherwise None.
    """
    if not isinstance(data, bytes):
        return f"payload data must be bytes (got {type(data).__name__})"
    if timeout is None or timeout <= 0:
        return f"timeout must be a positive number (got {timeout!r})"
    return None


def _udp_result_from_validation(host: str, port: int, error: str) -> UDPResult:
    """Build a failed UDPResult from a validation error."""
    logger.error(f"UDP test FAILED | Target: {host}:{port} | Message: {error}")
    return UDPResult(
        success=False,
        host=str(host),
        port=port,
        message=error,
        error_type="ValueError",
    )


def udp_send(
    host: str, port: int, data: bytes = b"probe", timeout: float = 1.0
) -> UDPResult:
    """
    Send a single UDP datagram to the target without waiting for a response.

    Args:
        host: Target IP address or hostname.
        port: Target UDP port.
        data: Payload bytes to transmit.
        timeout: Socket timeout in seconds (defensive; UDP sends are non-blocking).

    Returns:
        UDPResult: Structured result of the send operation.
    """
    error = _validate_target(host, port)
    if error is not None:
        return _udp_result_from_validation(host, port, error)
    error = _validate_udp_options(data, timeout)
    if error is not None:
        return _udp_result_from_validation(host, port, error)

    clean_host = host.strip()
    logger.info(f"Starting UDP send test to {clean_host}:{port}")

    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sent = sock.sendto(data, (clean_host, port))
        message = f"UDP packet sent ({sent} bytes) to {clean_host}:{port}"
        logger.info(f"UDP SEND | Target: {clean_host}:{port} | Result: SUCCESS | Message: {message}")
        return UDPResult(
            success=True,
            host=clean_host,
            port=port,
            message=message,
            sent=1,
        )
    except socket.gaierror as err:
        message = f"DNS resolution failed for hostname '{clean_host}' ({err})"
        logger.error(f"UDP SEND FAILED | Target: {clean_host}:{port} | Message: {message}")
        return UDPResult(
            success=False,
            host=clean_host,
            port=port,
            message=message,
            error_type="socket.gaierror",
        )
    except socket.timeout:
        message = f"UDP send timed out after {timeout} seconds"
        logger.error(f"UDP SEND FAILED | Target: {clean_host}:{port} | Message: {message}")
        return UDPResult(
            success=False,
            host=clean_host,
            port=port,
            message=message,
            error_type="socket.timeout",
        )
    except OSError as err:
        message = f"UDP socket error during send: {err}"
        logger.error(f"UDP SEND FAILED | Target: {clean_host}:{port} | Message: {message}")
        return UDPResult(
            success=False,
            host=clean_host,
            port=port,
            message=message,
            error_type="OSError",
        )
    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass


def udp_send_receive(
    host: str,
    port: int,
    data: bytes = b"probe",
    timeout: float = 1.0,
    buffer_size: int = DEFAULT_BUFFER_SIZE,
) -> UDPResult:
    """
    Send a UDP datagram and wait for a response, measuring round-trip latency.

    Args:
        host: Target IP address or hostname.
        port: Target UDP port.
        data: Payload bytes to transmit.
        timeout: Maximum time in seconds to wait for a UDP response.
        buffer_size: Receive buffer size in bytes.

    Returns:
        UDPResult: Structured result, including latency_ms when successful.
    """
    error = _validate_target(host, port)
    if error is not None:
        return _udp_result_from_validation(host, port, error)
    error = _validate_udp_options(data, timeout)
    if error is not None:
        return _udp_result_from_validation(host, port, error)

    clean_host = host.strip()
    logger.info(f"Starting UDP send/receive test to {clean_host}:{port}")

    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)

        start = time.perf_counter()
        sock.sendto(data, (clean_host, port))
        response, _ = sock.recvfrom(buffer_size)
        latency_ms = (time.perf_counter() - start) * 1000.0

        message = f"UDP response received ({len(response)} bytes) from {clean_host}:{port}"
        logger.debug(
            f"UDP packet sent to {clean_host}:{port}; latency measured: {latency_ms:.2f} ms"
        )
        logger.info(
            f"UDP SEND/RECEIVE | Target: {clean_host}:{port} | Result: SUCCESS | Message: {message}"
        )
        return UDPResult(
            success=True,
            host=clean_host,
            port=port,
            message=message,
            latency_ms=latency_ms,
            sent=1,
            received=1,
        )
    except socket.timeout:
        message = f"UDP response timeout after {timeout} seconds"
        logger.warning(f"UDP response timeout for {clean_host}:{port}")
        return UDPResult(
            success=False,
            host=clean_host,
            port=port,
            message=message,
            error_type="socket.timeout",
        )
    except socket.gaierror as err:
        message = f"DNS resolution failed for hostname '{clean_host}' ({err})"
        logger.error(f"UDP SEND/RECEIVE FAILED | Target: {clean_host}:{port} | Message: {message}")
        return UDPResult(
            success=False,
            host=clean_host,
            port=port,
            message=message,
            error_type="socket.gaierror",
        )
    except ConnectionResetError as err:
        # A closed UDP port may surface an ICMP port-unreachable as a reset.
        message = f"UDP target unreachable (connection reset): {err}"
        logger.error(f"UDP SEND/RECEIVE FAILED | Target: {clean_host}:{port} | Message: {message}")
        return UDPResult(
            success=False,
            host=clean_host,
            port=port,
            message=message,
            error_type="ConnectionResetError",
        )
    except OSError as err:
        message = f"UDP socket error: {err}"
        logger.error(f"UDP SEND/RECEIVE FAILED | Target: {clean_host}:{port} | Message: {message}")
        return UDPResult(
            success=False,
            host=clean_host,
            port=port,
            message=message,
            error_type="OSError",
        )
    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

