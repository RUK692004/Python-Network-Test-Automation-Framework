"""
Tests for network_tests.throughput (Phase 3).

Unit-style determinism tests use monkeypatching; integration-style tests use a
local TCP sink / UDP endpoints from conftest fixtures (no external network).
"""

import pytest

from network_tests.throughput import (
    ThroughputResult,
    UDPThroughputResult,
    measure_tcp_throughput,
    measure_udp_throughput,
)


@pytest.mark.throughput
class TestTcpThroughputValidation:
    """Input-validation paths raise ValueError instead of crashing."""

    @pytest.mark.parametrize("port", [0, -1, 65536, 999999])
    def test_invalid_port_raises(self, port):
        with pytest.raises(ValueError, match="Invalid port number"):
            measure_tcp_throughput("127.0.0.1", port, duration_seconds=0.5)

    @pytest.mark.parametrize(
        "duration", [0, -1.0, None]
    )
    def test_invalid_duration_raises(self, duration):
        with pytest.raises(ValueError, match="duration_seconds"):
            measure_tcp_throughput("127.0.0.1", 5001, duration_seconds=duration)

    def test_invalid_buffer_size_raises(self):
        with pytest.raises(ValueError, match="buffer_size"):
            measure_tcp_throughput("127.0.0.1", 5001, buffer_size=0)

    def test_empty_host_raises(self):
        with pytest.raises(ValueError, match="Invalid target host"):
            measure_tcp_throughput("   ", 5001, duration_seconds=0.5)

    def test_empty_data_chunk_raises(self):
        with pytest.raises(ValueError, match="data_chunk"):
            measure_tcp_throughput(
                "127.0.0.1", 5001, duration_seconds=0.5, data_chunk=b""
            )

    @pytest.mark.network
    def test_connection_refused(self, closed_port):
        host, port = closed_port
        result = measure_tcp_throughput(host, port, duration_seconds=0.2)
        assert isinstance(result, ThroughputResult)
        assert not result.success
        assert result.error_type is not None


@pytest.mark.throughput
@pytest.mark.network
class TestTcpThroughputIntegration:
    """Real throughput measurements against a local TCP sink server."""

    def test_successful_measurement(self, tcp_sink_server):
        host, port = tcp_sink_server
        result = measure_tcp_throughput(host, port, duration_seconds=0.3)
        assert isinstance(result, ThroughputResult)
        assert result.success
        assert result.actual_bytes > 0
        assert result.duration_seconds > 0
        assert result.mbps > 0
        assert result.message

    def test_throughput_on_loopback_exceeds_100mbps(self, tcp_sink_server):
        # Loopback sink on any modern machine should exceed 100 Mbps.
        host, port = tcp_sink_server
        result = measure_tcp_throughput(host, port, duration_seconds=0.3)
        assert result.success
        assert result.mbps > 100

    def test_result_consistency(self, tcp_sink_server):
        host, port = tcp_sink_server
        result = measure_tcp_throughput(host, port, duration_seconds=0.2)
        expected_bps = result.actual_bytes * 8 / result.duration_seconds
        assert result.bits_per_second == pytest.approx(expected_bps)
        assert result.gbps == pytest.approx(result.mbps / 1000.0)


@pytest.mark.throughput
class TestUdpThroughputValidation:
    """UDP transmit-mode validation."""

    @pytest.mark.parametrize("count", [0, -5])
    def test_invalid_packet_count_raises(self, count, udp_server):
        host, port = udp_server
        with pytest.raises(ValueError, match="packet_count"):
            measure_udp_throughput(host, port, packet_count=count)


@pytest.mark.throughput
@pytest.mark.network
class TestUdpThroughputIntegration:
    """
    UDP transmission-rate measurements against local targets.

    Note: udp.sendto() success only proves datagrams left the local stack -
    it does NOT confirm delivery. The measured rate is a *transmission* rate.
    """

    def test_transmit_to_local_target(self, udp_server):
        host, port = udp_server
        result = measure_udp_throughput(
            host, port, packet_count=50, payload=b"x" * 1024, timeout=1.0
        )
        assert isinstance(result, UDPThroughputResult)
        assert result.packets_ok == 50
        assert result.packets_sent == 50
        assert result.success
        assert result.mbps > 0
        assert result.duration_seconds > 0

    def test_partial_send_loss_windows_reset(self):
        # On Windows sending to an unused localhost port yields
        # ConnectionResetError; on Linux it silently succeeds or times out.
        # Both are valid outcomes - just assert internal consistency.
        import socket as _socket

        probe = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
        probe.bind(("127.0.0.1", 0))
        _, dead_port = probe.getsockname()
        probe.close()

        result = measure_udp_throughput(
            "127.0.0.1", dead_port, packet_count=10, timeout=0.05
        )
        assert result.packets_ok + result.packets_lost == 10
        if result.packets_lost > 0:
            assert "ConnectionResetError" in result.send_errors or (
                "TimeoutError" in result.send_errors
                or "OSError" in result.send_errors
            )
