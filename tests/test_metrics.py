"""
Automated pytest suite for packet-loss and latency metrics.
"""

from typing import Tuple

import pytest

from network_tests.metrics import (
    calculate_latency_stats,
    measure_udp_latency,
    packet_loss_percentage,
    LatencyStats,
)


@pytest.mark.metrics
def test_packet_loss_percentage():
    """
    Verify the packet-loss formula: (sent - received) / sent * 100.
    """
    assert packet_loss_percentage(sent=20, received=19) == pytest.approx(5.0)
    assert packet_loss_percentage(sent=5, received=5) == pytest.approx(0.0)
    assert packet_loss_percentage(sent=4, received=0) == pytest.approx(100.0)
    # No packets sent should not divide by zero / raise.
    assert packet_loss_percentage(sent=0, received=0) == 0.0


@pytest.mark.metrics
def test_calculate_latency_stats():
    """
    Verify aggregate latency statistics (min/max/avg) and loss calculation.
    """
    latencies = [20.8, 23.1, 21.4]
    stats = calculate_latency_stats(latencies, sent=5, received=3)

    assert isinstance(stats, LatencyStats)
    assert stats.sent == 5
    assert stats.received == 3
    assert stats.lost == 2
    assert stats.packet_loss_percent == pytest.approx(40.0)
    assert stats.min_latency_ms == pytest.approx(20.8)
    assert stats.max_latency_ms == pytest.approx(23.1)
    assert stats.average_latency_ms == pytest.approx(21.766666, abs=1e-3)
    assert stats.latencies_ms == latencies


@pytest.mark.metrics
def test_calculate_latency_stats_no_responses():
    """
    Verify stats handling when no responses were received.
    """
    stats = calculate_latency_stats([], sent=3, received=0)

    assert stats.lost == 3
    assert stats.packet_loss_percent == pytest.approx(100.0)
    assert stats.min_latency_ms is None
    assert stats.max_latency_ms is None
    assert stats.average_latency_ms is None


@pytest.mark.metrics
@pytest.mark.network
def test_measure_udp_latency_no_loss(udp_server: Tuple[str, int]):
    """
    Verify latency measurement against a full echo server yields zero loss and valid stats.
    """
    host, port = udp_server
    stats = measure_udp_latency(host=host, port=port, packet_count=5, timeout=0.5)

    assert isinstance(stats, LatencyStats)
    assert stats.sent == 5
    assert stats.received == 5
    assert stats.lost == 0
    assert stats.packet_loss_percent == pytest.approx(0.0)
    assert stats.min_latency_ms is not None
    assert stats.max_latency_ms is not None
    assert stats.average_latency_ms is not None
    assert stats.min_latency_ms <= stats.average_latency_ms <= stats.max_latency_ms
    assert stats.min_latency_ms >= 0.0


@pytest.mark.metrics
@pytest.mark.network
def test_measure_udp_latency_partial_loss(udp_drop_server: Tuple[str, int]):
    """
    Verify latency measurement detects partial packet loss deterministically.

    The drop server responds only to the first 2 of 5 packets, so 3 are lost.
    """
    host, port = udp_drop_server
    stats = measure_udp_latency(host=host, port=port, packet_count=5, timeout=0.3)

    assert stats.sent == 5
    assert stats.received == 2
    assert stats.lost == 3
    assert stats.packet_loss_percent == pytest.approx(60.0)


@pytest.mark.metrics
@pytest.mark.network
def test_measure_udp_latency_all_lost():
    """
    Verify latency measurement reports 100% loss when no endpoint responds.
    """
    import socket as _socket

    probe = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
    probe.bind(("127.0.0.1", 0))
    _, port = probe.getsockname()
    probe.close()

    stats = measure_udp_latency(host="127.0.0.1", port=port, packet_count=3, timeout=0.2)

    assert stats.sent == 3
    assert stats.received == 0
    assert stats.lost == 3
    assert stats.packet_loss_percent == pytest.approx(100.0)
    assert stats.average_latency_ms is None


@pytest.mark.metrics
@pytest.mark.parametrize("invalid_count", [0, -1])
def test_measure_udp_latency_invalid_packet_count(invalid_count: int):
    """
    Verify measurement rejects invalid (non-positive) packet counts.
    """
    with pytest.raises(ValueError):
        measure_udp_latency(host="127.0.0.1", port=5000, packet_count=invalid_count)


@pytest.mark.metrics
@pytest.mark.parametrize("invalid_timeout", [0, -1.0])
def test_measure_udp_latency_invalid_timeout(invalid_timeout: float):
    """
    Verify measurement rejects invalid (non-positive) timeouts.
    """
    with pytest.raises(ValueError):
        measure_udp_latency(
            host="127.0.0.1", port=5000, packet_count=1, timeout=invalid_timeout
        )
