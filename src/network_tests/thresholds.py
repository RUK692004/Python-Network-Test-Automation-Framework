"""
Performance threshold evaluation for Network Test Automation Framework.

Defines configurable thresholds for latency, packet loss, and throughput,
plus a reusable evaluator that compares a measured value against a threshold
and produces a structured verdict with diagnostic information.
"""

from dataclasses import dataclass
from typing import Dict, Optional

from utils.logger import get_logger

logger = get_logger("network_tests.thresholds")


@dataclass
class PerformanceThresholds:
    """
    Configurable performance thresholds.

    Latency and packet-loss thresholds are upper bounds (a measurement above
    the bound fails); throughput thresholds are lower bounds (a measurement
    below the bound fails).

    Attributes:
        max_average_latency_ms: Max allowed average latency in ms (None = not set).
        max_p95_latency_ms: Max allowed p95 latency in ms (None = not set).
        max_packet_loss_percent: Max allowed packet-loss % (None = not set).
        min_throughput_mbps: Min required throughput in Mbps (None = not set).
    """

    max_average_latency_ms: Optional[float] = None
    max_p95_latency_ms: Optional[float] = None
    max_packet_loss_percent: Optional[float] = None
    min_throughput_mbps: Optional[float] = None

    def effective(self) -> Dict[str, Optional[float]]:
        """Return a dict of only the thresholds that are actually configured."""
        return {
            name: value
            for name, value in {
                "max_average_latency_ms": self.max_average_latency_ms,
                "max_p95_latency_ms": self.max_p95_latency_ms,
                "max_packet_loss_percent": self.max_packet_loss_percent,
                "min_throughput_mbps": self.min_throughput_mbps,
            }.items()
            if value is not None
        }


@dataclass
class ThresholdResult:
    """
    Structured verdict from evaluating a single measurement against a threshold.

    Attributes:
        metric: Name of the metric being evaluated (e.g. 'latency.average_ms').
        measured: The measured value.
        threshold: The configured threshold value.
        passed: True if the measurement satisfies the threshold.
        message: Human-readable diagnostic message.
        unit: Optional unit string for the metric.
    """

    metric: str
    measured: float
    threshold: float
    passed: bool
    message: str
    unit: str = ""


def _format_value(value: float) -> str:
    """Format a float for readable diagnostics (no trailing zeros)."""
    return f"{value:.2f}".rstrip("0").rstrip(".")



def evaluate_latency_threshold(
    average_ms: Optional[float],
    p95_ms: Optional[float],
    thresholds: PerformanceThresholds,
) -> list:
    """
    Evaluate measured latency statistics against configured latency thresholds.

    Args:
        average_ms: Measured average latency in ms (or None).
        p95_ms: Measured p95 latency in ms (or None).
        thresholds: PerformanceThresholds with latency bounds.

    Returns:
        List of ThresholdResult, one per configured latency threshold.
    """
    results: list = []

    if thresholds.max_average_latency_ms is not None:
        if average_ms is None:
            results.append(
                ThresholdResult(
                    metric="latency.average_ms",
                    measured=0.0,
                    threshold=thresholds.max_average_latency_ms,
                    passed=False,
                    unit="ms",
                    message=(
                        f"Average latency unavailable (no successful samples), "
                        f"threshold {thresholds.max_average_latency_ms} ms cannot be satisfied"
                    ),
                )
            )
        else:
            passed = average_ms <= thresholds.max_average_latency_ms
            results.append(
                ThresholdResult(
                    metric="latency.average_ms",
                    measured=average_ms,
                    threshold=thresholds.max_average_latency_ms,
                    passed=passed,
                    unit="ms",
                    message=(
                        f"Average latency {_format_value(average_ms)} ms, "
                        f"maximum allowed {_format_value(thresholds.max_average_latency_ms)} ms"
                    ),
                )
            )

    if thresholds.max_p95_latency_ms is not None:
        if p95_ms is None:
            results.append(
                ThresholdResult(
                    metric="latency.p95_ms",
                    measured=0.0,
                    threshold=thresholds.max_p95_latency_ms,
                    passed=False,
                    unit="ms",
                    message=(
                        f"P95 latency unavailable (no successful samples), "
                        f"threshold {thresholds.max_p95_latency_ms} ms cannot be satisfied"
                    ),
                )
            )
        else:
            passed = p95_ms <= thresholds.max_p95_latency_ms
            results.append(
                ThresholdResult(
                    metric="latency.p95_ms",
                    measured=p95_ms,
                    threshold=thresholds.max_p95_latency_ms,
                    passed=passed,
                    unit="ms",
                    message=(
                        f"P95 latency {_format_value(p95_ms)} ms, "
                        f"maximum allowed {_format_value(thresholds.max_p95_latency_ms)} ms"
                    ),
                )
            )

    return results


def evaluate_packet_loss_threshold(
    loss_percent: float, max_percent: Optional[float]
) -> Optional[ThresholdResult]:
    """
    Evaluate measured packet-loss percentage against a configured threshold.

    Args:
        loss_percent: Measured packet-loss percentage.
        max_percent: Max allowed packet-loss percentage (None = not configured).

    Returns:
        ThresholdResult, or None if no threshold is configured.
    """
    if max_percent is None:
        return None
    passed = loss_percent <= max_percent
    return ThresholdResult(
        metric="packet_loss.percent",
        measured=loss_percent,
        threshold=max_percent,
        passed=passed,
        unit="%",
        message=(
            f"Packet loss {_format_value(loss_percent)}%, "
            f"maximum allowed {_format_value(max_percent)}%"
        ),
    )


def evaluate_throughput_threshold(
    throughput_mbps: float, min_mbps: Optional[float]
) -> Optional[ThresholdResult]:
    """
    Evaluate measured throughput against a configured minimum threshold.

    Args:
        throughput_mbps: Measured throughput in Mbps.
        min_mbps: Min required throughput in Mbps (None = not configured).

    Returns:
        ThresholdResult, or None if no threshold is configured.
    """
    if min_mbps is None:
        return None
    passed = throughput_mbps >= min_mbps
    return ThresholdResult(
        metric="throughput.mbps",
        measured=throughput_mbps,
        threshold=min_mbps,
        passed=passed,
        unit="Mbps",
        message=(
            f"Throughput {_format_value(throughput_mbps)} Mbps, "
            f"required minimum {_format_value(min_mbps)} Mbps"
        ),
    )

