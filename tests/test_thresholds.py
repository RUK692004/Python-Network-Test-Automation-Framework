"""
Unit tests for network_tests.thresholds (Phase 3).

Deterministic threshold-evaluation tests - no networking involved.
"""

import pytest

from network_tests.thresholds import (
    PerformanceThresholds,
    evaluate_latency_threshold,
    evaluate_packet_loss_threshold,
    evaluate_throughput_threshold,
)


@pytest.mark.performance
class TestThroughputThreshold:
    """Throughput threshold: lower bound (fail below)."""

    def test_pass_above_threshold(self):
        result = evaluate_throughput_threshold(55.0, min_mbps=50.0)
        assert result.passed
        assert "Mbps" in result.unit

    def test_fail_below_threshold(self):
        result = evaluate_throughput_threshold(42.3, min_mbps=50.0)
        assert not result.passed
        assert "42.3" in result.message and "50" in result.message

    def test_no_threshold_configured_returns_none(self):
        assert evaluate_throughput_threshold(10.0, min_mbps=None) is None

    def test_exact_threshold_passes(self):
        assert evaluate_throughput_threshold(50.0, min_mbps=50.0).passed


@pytest.mark.latency
class TestLatencyThreshold:
    """Latency thresholds: upper bounds (fail above)."""

    def test_both_pass(self):
        thresholds = PerformanceThresholds(
            max_average_latency_ms=100.0, max_p95_latency_ms=150.0
        )
        results = evaluate_latency_threshold(50.0, 120.0, thresholds)
        assert len(results) == 2
        assert all(r.passed for r in results)

    def test_average_fails(self):
        thresholds = PerformanceThresholds(max_average_latency_ms=100.0)
        results = evaluate_latency_threshold(126.4, None, thresholds)
        assert len(results) == 1
        assert not results[0].passed
        assert "Average latency" in results[0].message

    def test_p95_fails(self):
        thresholds = PerformanceThresholds(max_p95_latency_ms=150.0)
        results = evaluate_latency_threshold(20.0, 181.2, thresholds)
        assert not results[0].passed

    def test_none_samples_fail_when_threshold_set(self):
        thresholds = PerformanceThresholds(max_average_latency_ms=100.0)
        results = evaluate_latency_threshold(None, None, thresholds)
        assert all(not r.passed for r in results)

    def test_no_thresholds_returns_empty(self):
        thresholds = PerformanceThresholds()
        assert evaluate_latency_threshold(1.0, 1.0, thresholds) == []


@pytest.mark.packet_loss
class TestPacketLossThreshold:
    """Packet-loss threshold: upper bound."""

    def test_pass_within_threshold(self):
        result = evaluate_packet_loss_threshold(3.0, max_percent=5.0)
        assert result.passed

    def test_fail_over_threshold(self):
        result = evaluate_packet_loss_threshold(8.0, max_percent=5.0)
        assert not result.passed
        assert "8" in result.message and "5" in result.message

    def test_not_configured_returns_none(self):
        assert evaluate_packet_loss_threshold(99.0, max_percent=None) is None


@pytest.mark.performance
class TestPerformanceThresholdsDefaults:
    """Sanity checks on the threshold container itself."""

    def test_all_defaults_unset(self):
        thresholds = PerformanceThresholds()
        assert thresholds.effective() == {}

    def test_effective_only_lists_configured(self):
        thresholds = PerformanceThresholds(min_throughput_mbps=10.0)
        assert thresholds.effective() == {"min_throughput_mbps": 10.0}
