"""
Port availability test module for Network Test Automation Framework.

Checks whether a target TCP port is open, closed (refused), timed out,
or unreachable due to host/DNS resolution errors.
"""

from dataclasses import dataclass
import socket
from typing import Optional

from utils.logger import get_logger

logger = get_logger("network_tests.port")


@dataclass
class PortStatusResult:
    """
    Data class representing the result of a port availability check.

    Attributes:
        target: Target IP address or hostname.
        port: Target TCP port.
        is_open: True if the port is reachable and accepted connection.
        state: OPEN, CLOSED, TIMEOUT, INVALID_HOST, or ERROR.
        message: Descriptive summary of port state.
        error_detail: Optional details regarding error encountered.
    """

    target: str
    port: int
    is_open: bool
    state: str
    message: str
    error_detail: Optional[str] = None


def check_port_availability(
    host: str, port: int, timeout: float = 3.0
) -> PortStatusResult:
    """
    Determine whether a specific TCP port on a target host is open and reachable.

    Args:
        host: Target IP address or hostname.
        port: Target TCP port number.
        timeout: Socket connection timeout in seconds.

    Returns:
        PortStatusResult: Categorized status of the target port.
    """
    logger.info(f"Starting port availability test for {host}:{port} (timeout={timeout}s)")

    if not host or not isinstance(host, str) or not host.strip():
        msg = "Invalid target host provided"
        logger.error(f"PORT AVAILABILITY TEST FAILED | Target: {host}:{port} | Message: {msg}")
        return PortStatusResult(
            target=str(host),
            port=port,
            is_open=False,
            state="INVALID_HOST",
            message=msg,
            error_detail=msg,
        )

    if not isinstance(port, int) or not (1 <= port <= 65535):
        msg = f"Invalid port number: {port}. Port must be between 1 and 65535."
        logger.error(f"PORT AVAILABILITY TEST FAILED | Target: {host}:{port} | Message: {msg}")
        return PortStatusResult(
            target=host,
            port=port,
            is_open=False,
            state="ERROR",
            message=msg,
            error_detail=msg,
        )

    clean_host = host.strip()
    sock = None

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        # connect_ex returns 0 on success, or errno on failure
        result_code = sock.connect_ex((clean_host, port))

        if result_code == 0:
            msg = f"Port {port} is OPEN"
            logger.info(f"PORT AVAILABILITY TEST | Target: {clean_host}:{port} | Result: OPEN")
            return PortStatusResult(
                target=clean_host,
                port=port,
                is_open=True,
                state="OPEN",
                message=msg,
            )
        else:
            msg = f"Port {port} is CLOSED (connection refused or rejected, errno={result_code})"
            logger.info(f"PORT AVAILABILITY TEST | Target: {clean_host}:{port} | Result: CLOSED")
            return PortStatusResult(
                target=clean_host,
                port=port,
                is_open=False,
                state="CLOSED",
                message=msg,
                error_detail=f"errno={result_code}",
            )

    except socket.timeout:
        msg = f"Port check timed out after {timeout} seconds"
        logger.warning(f"PORT AVAILABILITY TEST | Target: {clean_host}:{port} | Result: TIMEOUT")
        return PortStatusResult(
            target=clean_host,
            port=port,
            is_open=False,
            state="TIMEOUT",
            message=msg,
            error_detail=msg,
        )

    except socket.gaierror as err:
        msg = f"Invalid target or host resolution failure: {err}"
        logger.error(f"PORT AVAILABILITY TEST | Target: {clean_host}:{port} | Result: INVALID_HOST")
        return PortStatusResult(
            target=clean_host,
            port=port,
            is_open=False,
            state="INVALID_HOST",
            message=msg,
            error_detail=str(err),
        )

    except OSError as err:
        msg = f"Socket error checking port status: {err}"
        logger.error(f"PORT AVAILABILITY TEST | Target: {clean_host}:{port} | Result: ERROR")
        return PortStatusResult(
            target=clean_host,
            port=port,
            is_open=False,
            state="ERROR",
            message=msg,
            error_detail=str(err),
        )

    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
