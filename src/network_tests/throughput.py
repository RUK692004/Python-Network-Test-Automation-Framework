"""
Throughput measurement module for Network Test Automation Framework.

Measures the amount of data actually transferred over a network connection
during a defined period using Python sockets only (no external tools required).
Throughput is always computed from real transferred bytes, never a theoretical
link speed.
"""

from dataclasses import dataclass
import socket
import time
from typing import Optional

from utils.logger import get_logger

logger = get_logger("network_tests.throughput")

BITS_PER_BYTE = 8
MEGA = 1_000_000
GIGA = 1_000_000_000

DEFAULT_TCP_BUFFER = 65536


@dataclass
class ThroughputResult:
    """
    Structured result of a throughput measurement.

    Attributes:
        success: True if the measurement completed (or failed gracefully).
        protocol: 'tcp' or 'udp'.
        actual_bytes: Total bytes successfully transferred.
        duration_seconds: Elapsed measurement time in seconds.
        bits_per_second: Throughput in bits/second.
        mbps: Throughput in Mbps (megabits per second).
        gbps: Throughput in Gbps (gigabits per second; 0 when tiny).
        message: Human-readable summary.
        error_type: Exception/condition name if the measurement failed.
    """

    success: bool
    protocol: str
    actual_bytes: int
    duration_seconds: float
    bits_per_second: float
    mbps: float
    gbps: float
    message: str
    error_type: Optional[str] = None


def _throughput_convert(actual_bytes: int, duration_seconds: float) -> tuple:
    """
    Convert transferred bytes and elapsed seconds into bps / Mbps / Gbps.

    Args:
        actual_bytes: Number of bytes transferred.
        duration_seconds: Elapsed time in seconds.

    Returns:
        Tuple of (bits_per_second, mbps, gbps).
    """
    if duration_seconds <= 0:
        return 0.0, 0.0, 0.0
    bps = (actual_bytes * BITS_PER_BYTE) / duration_seconds
    return bps, bps / MEGA, bps / GIGA


def _validate_throughput_config(
    duration_seconds: float, buffer_size: int
) -> Optional[str]:
    """Validate throughput test parameters, returning an error string or None."""
    if duration_seconds is None or duration_seconds <= 0:
        return (
            f"duration_seconds must be a positive number "
            f"(got {duration_seconds!r})"
        )
    if not isinstance(buffer_size, int) or buffer_size <= 0:
        return (
            f"buffer_size must be a positive integer (got {buffer_size!r})"
        )
    return None


def _validate_host_port(host: str, port: int) -> Optional[str]:
    """Validate a host/port pair for throughput tests."""
    if not isinstance(host, str) or not host.strip():
        return "Invalid target host provided"
    if not isinstance(port, int) or not (1 <= port <= 65535):
        return (
            f"Invalid port number: {port}. Port must be between 1 and 65535."
        )
    return None



def measure_tcp_throughput(
    host: str,
    port: int,
    duration_seconds: float = 2.0,
    buffer_size: int = DEFAULT_TCP_BUFFER,
    data_chunk: bytes = b"x" * DEFAULT_TCP_BUFFER,
) -> ThroughputResult:
    """
    Measure TCP throughput by pushing data to a target for a defined duration.

    Args:
        host: Target IP address or hostname.
        port: Target TCP port.
        duration_seconds: How long (in seconds) to send data.
        buffer_size: Socket send buffer size hint.
        data_chunk: Bytes to send repeatedly (must be non-empty bytes).

    Returns:
        ThroughputResult: Achieved throughput based on real transferred bytes.

    Raises:
        ValueError: If the target, duration, buffer, or data chunk is invalid.
    """
    error = _validate_host_port(host, port)
    if error is not None:
        raise ValueError(error)
    error = _validate_throughput_config(duration_seconds, buffer_size)
    if error is not None:
        raise ValueError(error)
    if not isinstance(data_chunk, bytes) or not data_chunk:
        raise ValueError(
            f"data_chunk must be non-empty bytes (got {type(data_chunk).__name__})"
        )

    clean_host = host.strip()
    logger.info(f"Starting TCP throughput test to {clean_host}:{port}")
    logger.info(f"Duration: {duration_seconds} seconds, buffer size: {buffer_size}")

    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(duration_seconds + 5.0)
        sock.connect((clean_host, port))

        start = time.perf_counter()
        actual_bytes = 0
        while (time.perf_counter() - start) < duration_seconds:
            sent = sock.send(data_chunk)
            if sent <= 0:
                break
            actual_bytes += sent

        elapsed = time.perf_counter() - start
        bits_per_second, mbps, gbps = _throughput_convert(actual_bytes, elapsed)

        message = (
            f"TCP throughput: {mbps:.2f} Mbps "
            f"({actual_bytes} bytes in {elapsed:.3f}s)"
        )
        logger.info(f"Bytes transferred: {actual_bytes}")
        logger.info(f"Throughput: {mbps:.2f} Mbps")
        return ThroughputResult(
            success=True,
            protocol="tcp",
            actual_bytes=actual_bytes,
            duration_seconds=elapsed,
            bits_per_second=bits_per_second,
            mbps=mbps,
            gbps=gbps,
            message=message,
        )
    except socket.timeout:
        return _tcp_tp_failure(
            clean_host, port, duration_seconds, "socket.timeout",
            f"TCP throughput test timed out after {duration_seconds}s",
        )
    except (ConnectionRefusedError, ConnectionResetError, BrokenPipeError) as err:
        return _tcp_tp_failure(
            clean_host, port, duration_seconds, type(err).__name__,
            f"TCP connection lost during throughput test: {err}",
        )
    except socket.gaierror as err:
        return _tcp_tp_failure(
            clean_host, port, duration_seconds, "socket.gaierror",
            f"DNS resolution failed for hostname '{clean_host}' ({err})",
        )
    except OSError as err:
        return _tcp_tp_failure(
            clean_host, port, duration_seconds, "OSError",
            f"Socket error during TCP throughput test: {err}",
        )
    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass




def _tcp_tp_failure(
    host: str,
    port: int,
    duration_seconds: float,
    error_type: str,
    message: str,
) -> ThroughputResult:
    """Build a failed ThroughputResult for a TCP throughput failure."""
    logger.error(message)
    return ThroughputResult(
        success=False,
        protocol="tcp",
        actual_bytes=0,
        duration_seconds=duration_seconds,
        bits_per_second=0.0,
        mbps=0.0,
        gbps=0.0,
        message=message,
        error_type=error_type,
    )


def measure_udp_throughput(
    host: str,
    port: int,
    packet_count: int = 100,
    payload: bytes = b"x" * 1024,
    timeout: float = 1.0,
) -> "UDPThroughputResult":
    """
    Measure UDP transmission via `sendto`, reporting packets sent and duration.

    UDP throughput is fundamentally different from TCP: `sendto` success only
    means the datagram left the local stack, not that a peer received it. This
    function therefore reports *transmitted* packets and rate and does NOT
    claim confirmed delivery.

    Args:
        host: Target IP address or hostname.
        port: Target UDP port.
        packet_count: Number of datagrams to send.
        payload: Datagram payload bytes.
        timeout: Socket send timeout.

    Returns:
        UDPThroughputResult: Transmission statistics.
    """
    from network_tests.udp import udp_send

    if not isinstance(packet_count, int) or packet_count <= 0:
        raise ValueError(f"packet_count must be a positive integer (got {packet_count!r})")

    logger.info(
        f"Starting UDP throughput test to {host}:{port} ({packet_count} packets)"
    )
    sent_ok = 0
    start = time.perf_counter()
    errors: list = []

    for _ in range(packet_count):
        result = udp_send(host=host, port=port, data=payload, timeout=timeout)
        if result.success:
            sent_ok += 1
        else:
            errors.append(result.error_type)

    elapsed = time.perf_counter() - start
    transferred_bytes = sent_ok * len(payload)
    bps, mbps, gbps = _throughput_convert(transferred_bytes, elapsed)

    if not errors:
        message = f"UDP transmit: {sent_ok}/{packet_count} packets ({mbps:.2f} Mbps)"
    else:
        message = (
            f"UDP transmit: {sent_ok}/{packet_count} packets, "
            f"{len(errors)} send errors ({mbps:.2f} Mbps)"
        )
    logger.info(message)

    return UDPThroughputResult(
        success=sent_ok == packet_count,
        protocol="udp",
        packets_sent=packet_count,
        packets_ok=sent_ok,
        packets_lost=packet_count - sent_ok,
        payload_bytes=len(payload),
        duration_seconds=elapsed,
        bits_per_second=bps,
        mbps=mbps,
        gbps=gbps,
        message=message,
        send_errors=errors,
    )




@dataclass
class UDPThroughputResult:
    """
    Result of a UDP throughput (transmission) measurement.

    Attributes:
        success: True if all datagrams were accepted by the local stack.
        protocol: Always 'udp'.
        packets_sent: Number of datagrams requested.
        packets_ok: Datagrams accepted by sendto.
        packets_lost: Datagrams that failed to send.
        payload_bytes: Size of each datagram payload.
        duration_seconds: Elapsed transmission time.
        bits_per_second / mbps / gbps: Transmission rate based on payload bytes.
        message: Human-readable summary.
        send_errors: List of error types encountered (empty when none).
    """

    success: bool
    protocol: str
    packets_sent: int
    packets_ok: int
    packets_lost: int
    payload_bytes: int
    duration_seconds: float
    bits_per_second: float
    mbps: float
    gbps: float
    message: str
    send_errors: Optional[list] = None

