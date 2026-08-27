"""
Unit tests for network_tests.statistics (Phase 3).

Deterministic statistical calculations only - no networking involved.
"""

import pytest

from network_tests.statistics import (
    LatencyStatistics,
    PacketLossStatistics,
    calculate_latency_statistics,
    calculate_packet_loss_statistics,
    percentile,
)


@pytest.mark.latency
class TestPercentile:
    """Tests for the reusable percentile function."""

    def test_percentile_single_sample(self):
        assert percentile([10.0], 95) == 10.0

    def test_percentile_interpolated(self):
        # rank = 0.5 * (3 - 1) = 1.0 -> exact middle value
        assert percentile([1.0, 2.0, 3.0], 50) == 2.0

    def test_percentile_max_is_last(self):
        data = [1.0] * 99 + [100.0]
        assert percentile(data, 100) == 100.0

    @pytest.mark.parametrize("pct", [0, -5, 101])
    def test_percentile_invalid_pct_raises(self, pct):
        with pytest.raises(ValueError):
            percentile([1.0, 2.0], pct)

    def test_percentile_empty_returns_none(self):
        assert percentile([], 95) is None


@pytest.mark.latency
class TestLatencyStatistics:
    """Tests for extended latency statistics."""

    def test_basic_statistics(self):
        stats = calculate_latency_statistics([10.0, 20.0, 30.0, 40.0])
        assert isinstance(stats, LatencyStatistics)
        assert stats.samples == 4
        assert stats.min_ms == 10.0
        assert stats.max_ms == 40.0
        assert stats.average_ms == pytest.approx(25.0)
        assert stats.median_ms == pytest.approx(25.0)

    def test_stddev_zero_for_identical_samples(self):
        stats = calculate_latency_statistics([5.0] * 10)
        assert stats.stddev_ms == 0.0

    def test_stddev_none_for_single_sample(self):
        stats = calculate_latency_statistics([7.5])
        assert stats.stddev_ms is None
        assert stats.p95_ms == 7.5

    def test_p95_p99_within_bounds(self):
        latencies = [float(i) for i in range(1, 101)]  # 1..100 ms
        stats = calculate_latency_statistics(latencies)
        assert 90 <= stats.p95_ms <= 100
        assert 96 <= stats.p99_ms <= 100
        assert stats.min_ms <= stats.median_ms <= stats.max_ms

    def test_empty_list_all_none(self):
        stats = calculate_latency_statistics([])
        assert stats.samples == 0
        for field in (
            stats.min_ms,
            stats.max_ms,
            stats.average_ms,
            stats.median_ms,
            stats.stddev_ms,
            stats.p95_ms,
            stats.p99_ms,
        ):
            assert field is None


@pytest.mark.packet_loss
class TestPacketLossStatistics:
    """Tests for packet-loss statistics wrapper."""

    def test_partial_loss(self):
        stats = calculate_packet_loss_statistics(sent=100, received=97)
        assert isinstance(stats, PacketLossStatistics)
        assert stats.sent == 100
        assert stats.received == 97
        assert stats.lost == 3
        assert stats.loss_percent == pytest.approx(3.0)

    def test_zero_loss(self):
        stats = calculate_packet_loss_statistics(sent=50, received=50)
        assert stats.lost == 0
        assert stats.loss_percent == 0.0

    def test_full_loss(self):
        stats = calculate_packet_loss_statistics(sent=20, received=0)
        assert stats.lost == 20
        assert stats.loss_percent == 100.0

    def test_received_exceeding_sent_clamped(self):
        # Defensive: received must never produce negative loss.
        stats = calculate_packet_loss_statistics(sent=10, received=12)
        assert stats.lost == 0
        assert stats.loss_percent == 0.0
