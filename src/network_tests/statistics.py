"""
Network statistics module for Network Test Automation Framework.

Provides reusable statistical calculations on top of the existing metrics
module: latency statistics (median, standard deviation, percentiles) and
packet-loss statistics. Kept independent from pytest so it can be reused by
reporting and threshold logic.
"""

from dataclasses import dataclass
import statistics
from typing import List, Optional

from network_tests.metrics import packet_loss_percentage, LatencyStats
from utils.logger import get_logger

logger = get_logger("network_tests.statistics")


@dataclass
class LatencyStatistics:
    """
    Extended latency statistics over a set of latency samples.

    Attributes:
        samples: Total number of latency samples collected.
        min_ms: Minimum latency in ms (None if no samples).
        max_ms: Maximum latency in ms (None if no samples).
        average_ms: Arithmetic mean latency in ms (None if no samples).
        median_ms: Median latency in ms (None if no samples).
        stddev_ms: Population standard deviation in ms (None if < 2 samples).
        p95_ms: 95th percentile latency in ms (None if no samples).
        p99_ms: 99th percentile latency in ms (None if no samples).
    """

    samples: int
    min_ms: Optional[float]
    max_ms: Optional[float]
    average_ms: Optional[float]
    median_ms: Optional[float]
    stddev_ms: Optional[float]
    p95_ms: Optional[float]
    p99_ms: Optional[float]


@dataclass
class PacketLossStatistics:
    """
    Packet-loss statistics over a set of sent/received packets.

    Attributes:
        sent: Total packets sent.
        received: Total packets received.
        lost: Packets lost (sent - received).
        loss_percent: Packet-loss percentage (0.0 - 100.0).
    """

    sent: int
    received: int
    lost: int
    loss_percent: float


def percentile(samples: List[float], pct: float) -> Optional[float]:
    """
    Compute the ``pct``-th percentile of ``samples`` using linear interpolation.

    Mirrors NumPy's default NEAREST/linear behavior: for a rank-like
    calculation ``index = (pct/100) * (n - 1)``, interpolating between the
    floor and ceil neighbours.

    Args:
        samples: List of numeric samples.
        pct: Percentile to compute, in range (0, 100].

    Returns:
        The interpolated percentile value, or None if samples is empty.

    Raises:
        ValueError: If pct is not in (0, 100].
    """
    if not samples:
        return None
    if not (0 < pct <= 100):
        raise ValueError(f"pct must be in (0, 100], got {pct!r}")

    data = sorted(samples)
    n = len(data)
    if n == 1:
        return float(data[0])

    rank = (pct / 100.0) * (n - 1)
    lower = int(rank)
    upper = lower + 1
    if upper >= n:
        return float(data[-1])

    weight = rank - lower
    return float(data[lower] * (1.0 - weight) + data[upper] * weight)


def calculate_latency_statistics(latencies_ms: List[float]) -> LatencyStatistics:
    """
    Compute extended latency statistics from a list of latency samples.

    Args:
        latencies_ms: List of latency measurements in milliseconds.

    Returns:
        LatencyStatistics: Extended latency statistics.
    """
    if not latencies_ms:
        return LatencyStatistics(
            samples=0,
            min_ms=None,
            max_ms=None,
            average_ms=None,
            median_ms=None,
            stddev_ms=None,
            p95_ms=None,
            p99_ms=None,
        )

    data = list(latencies_ms)
    stddev = None
    if len(data) >= 2:
        stddev = statistics.pstdev(data)

    return LatencyStatistics(
        samples=len(data),
        min_ms=min(data),
        max_ms=max(data),
        average_ms=sum(data) / len(data),
        median_ms=statistics.median(data),
        stddev_ms=stddev,
        p95_ms=percentile(data, 95),
        p99_ms=percentile(data, 99),
    )


def calculate_packet_loss_statistics(
    sent: int, received: int
) -> PacketLossStatistics:
    """
    Compute packet-loss statistics from sent/received counts.

    Args:
        sent: Total packets sent.
        received: Total packets received.

    Returns:
        PacketLossStatistics: Sent/received/lost counts and loss percentage.
    """
    return PacketLossStatistics(
        sent=sent,
        received=received,
        lost=max(0, sent - received),
        loss_percent=packet_loss_percentage(sent, received),
    )


def stats_to_dict(stats: LatencyStatistics) -> dict:
    """Convert a LatencyStatistics object to a plain dict (useful for reporting)."""
    return {
        "samples": stats.samples,
        "min_ms": stats.min_ms,
        "max_ms": stats.max_ms,
        "average_ms": stats.average_ms,
        "median_ms": stats.median_ms,
        "stddev_ms": stats.stddev_ms,
        "p95_ms": stats.p95_ms,
        "p99_ms": stats.p99_ms,
    }
