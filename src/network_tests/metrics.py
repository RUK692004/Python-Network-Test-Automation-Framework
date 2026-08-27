"""
Network metrics module for Network Test Automation Framework.

Provides packet-loss measurement and request/response latency statistics.
Measurement logic is kept independent from pytest so it can be reused by
later phases (performance thresholds, HTML/JSON/CSV reporting).
"""

from dataclasses import dataclass, field
from typing import List, Optional

from network_tests.udp import DEFAULT_BUFFER_SIZE, udp_send_receive
from utils.logger import get_logger

logger = get_logger("network_tests.metrics")


@dataclass
class LatencyStats:
    """
    Aggregate statistics from a packet-loss / latency measurement run.

    Attributes:
        sent: Total packets sent.
        received: Packets that received a response.
        lost: Packets that did not receive a response.
        packet_loss_percent: Percentage of packets lost (0.0 - 100.0).
        min_latency_ms: Minimum round-trip latency in ms, or None if none received.
        max_latency_ms: Maximum round-trip latency in ms, or None if none received.
        average_latency_ms: Mean round-trip latency in ms, or None if none received.
        latencies_ms: List of measured latencies per successful packet.
    """

    sent: int
    received: int
    lost: int
    packet_loss_percent: float
    min_latency_ms: Optional[float]
    max_latency_ms: Optional[float]
    average_latency_ms: Optional[float]
    latencies_ms: List[float] = field(default_factory=list)


def packet_loss_percentage(sent: int, received: int) -> float:
    """
    Calculate the percentage of packets lost.

    Args:
        sent: Number of packets sent.
        received: Number of packets successfully received.

    Returns:
        Packet loss percentage (0.0 - 100.0). Returns 0.0 if no packets were sent.
    """
    if sent <= 0:
        return 0.0
    return (sent - received) / sent * 100.0


def calculate_latency_stats(
    latencies_ms: List[float], sent: int, received: int
) -> LatencyStats:
    """
    Compute aggregate latency statistics from a list of per-packet latencies.

    Args:
        latencies_ms: List of measured round-trip latencies in milliseconds.
        sent: Total packets sent.
        received: Total packets that received a response.

    Returns:
        LatencyStats: Calculated minimum, maximum, and average latency plus loss.
    """
    if latencies_ms:
        min_latency = min(latencies_ms)
        max_latency = max(latencies_ms)
        average_latency = sum(latencies_ms) / len(latencies_ms)
    else:
        min_latency = max_latency = average_latency = None

    loss_percent = packet_loss_percentage(sent, received)

    return LatencyStats(
        sent=sent,
        received=received,
        lost=sent - received,
        packet_loss_percent=loss_percent,
        min_latency_ms=min_latency,
        max_latency_ms=max_latency,
        average_latency_ms=average_latency,
        latencies_ms=list(latencies_ms),
    )



def _measure_udp_latency(
    host: str,
    port: int,
    packet_count: int,
    timeout: float = 1.0,
    buffer_size: int = DEFAULT_BUFFER_SIZE,
    payload: bytes = b"latency probe",
) -> LatencyStats:
    """
    Measure UDP round-trip latency over a series of packets against a UDP endpoint.

    Args:
        host: Target IP address or hostname.
        port: Target UDP port.
        packet_count: Number of UDP packets to send.
        timeout: Per-packet response timeout in seconds.
        buffer_size: Receive buffer size in bytes.
        payload: Payload bytes to send for each probe.

    Returns:
        LatencyStats: Loss and latency statistics for the measurement run.

    Raises:
        ValueError: If packet_count is not positive or timeout is not positive.
    """
    if not isinstance(packet_count, int) or packet_count <= 0:
        raise ValueError(
            f"packet_count must be a positive integer (got {packet_count!r})"
        )
    if timeout is None or timeout <= 0:
        raise ValueError(f"timeout must be a positive number (got {timeout!r})")

    logger.info(
        f"Starting UDP latency measurement to {host}:{port} "
        f"(packets={packet_count}, timeout={timeout}s)"
    )

    latencies: List[float] = []
    received = 0

    for index in range(1, packet_count + 1):
        logger.debug(f"Sending UDP packet {index}/{packet_count}")
        result = udp_send_receive(
            host=host,
            port=port,
            data=payload,
            timeout=timeout,
            buffer_size=buffer_size,
        )
        if result.success and result.latency_ms is not None:
            received += 1
            latencies.append(result.latency_ms)
        else:
            logger.warning(f"Packet {index}/{packet_count} lost: {result.message}")

    stats = calculate_latency_stats(latencies, sent=packet_count, received=received)
    logger.info(
        f"UDP latency measurement completed: sent={stats.sent}, received={stats.received}, "
        f"lost={stats.lost}, loss%={stats.packet_loss_percent:.2f}, "
        f"avg_latency={_format_ms(stats.average_latency_ms)}"
    )
    return stats


def measure_udp_latency(
    host: str,
    port: int,
    packet_count: int,
    timeout: float = 1.0,
    buffer_size: int = DEFAULT_BUFFER_SIZE,
    payload: bytes = b"latency probe",
) -> LatencyStats:
    """
    Send ``packet_count`` UDP probes to the target and return aggregate loss/latency stats.

    Args:
        host: Target IP address or hostname.
        port: Target UDP port.
        packet_count: Number of UDP packets to send.
        timeout: Per-packet response timeout in seconds.
        buffer_size: Receive buffer size in bytes.
        payload: Payload bytes to send for each probe.

    Returns:
        LatencyStats: Loss and latency statistics for the measurement run.

    Raises:
        ValueError: If packet_count or timeout is invalid.
    """
    return _measure_udp_latency(
        host=host,
        port=port,
        packet_count=packet_count,
        timeout=timeout,
        buffer_size=buffer_size,
        payload=payload,
    )


def _format_ms(value: Optional[float]) -> str:
    """Format an optional millisecond value for logging."""
    return "n/a" if value is None else f"{value:.2f} ms"

