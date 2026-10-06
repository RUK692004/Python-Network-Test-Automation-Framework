"""
Pytest suite for the canonical `TestResult` contract and the
`NetworkTestRunner` orchestration layer (Phase 1).
"""

from typing import Tuple

import pytest

from network_tests.results import TestResult
from network_tests.runner import NetworkTestRunner
from network_tests.runner import TestConfig as RunnerConfig


@pytest.fixture
def runner() -> NetworkTestRunner:
    """Provide a default-configured NetworkTestRunner."""
    return NetworkTestRunner()


class TestResultContract:
    """Pure unit tests for the shared result model."""

    def test_success_factory_fields(self):
        result = TestResult.success(
            test_name="Ping",
            target="127.0.0.1",
            latency_ms=1.5,
            duration_ms=12.25,
            metadata={"is_reachable": True},
        )

        assert isinstance(result, TestResult)
        assert result.status == TestResult.STATUS_PASS
        assert result.is_success is True
        assert result.test_name == "Ping"
        assert result.target == "127.0.0.1"
        assert result.latency_ms == 1.5
        assert result.duration_ms == 12.25
        assert result.error is None
        assert isinstance(result.metadata, dict)
        assert result.metadata == {"is_reachable": True}

    def test_failure_factory_fields(self):
        result = TestResult.failure(
            test_name="TCP Connectivity",
            target="example.com:443",
            message="Connection refused",
            duration_ms=3.5,
        )

        assert result.status == TestResult.STATUS_FAIL
        assert result.is_success is False
        assert result.error == "Connection refused"
        assert result.duration_ms == 3.5
        assert result.metadata == {}

    def test_round_trip_through_dict(self):
        original = TestResult.success(
            test_name="Port Check",
            target="10.0.0.1:22",
            latency_ms=2.0,
            duration_ms=4.0,
            metadata={"state": "OPEN", "port": 22},
        )

        restored = TestResult.from_dict(original.to_dict())

        assert restored == original
        assert isinstance(restored.metadata, dict)
        assert restored.metadata["state"] == "OPEN"

    def test_metadata_defaults_to_empty_dict(self):
        result = TestResult.success(test_name="t", target="x")

        assert isinstance(result.metadata, dict)
        assert result.metadata == {}


class TestRunnerConfig:
    """Runner-level configuration container tests."""

    def test_from_dict_applies_overrides(self):
        config = RunnerConfig.from_dict({"timeout": 9.5, "default_protocol": "udp"})

        assert config.timeout == 9.5
        assert config.default_protocol == "udp"

    def test_from_dict_uses_defaults(self):
        config = RunnerConfig.from_dict({})

        assert config.timeout == 3.0
        assert config.default_protocol == "tcp"
        assert config.log_level == "INFO"


class TestRunnerDispatch:
    """End-to-end dispatch through `NetworkTestRunner.run()`."""

    @pytest.mark.runner
    @pytest.mark.network
    def test_invalid_test_type_raises_value_error(self, runner):
        with pytest.raises(ValueError) as excinfo:
            runner.run("dns", "example.com")

        assert "Unsupported test type" in str(excinfo.value)

    @pytest.mark.runner
    def test_non_string_target_raises_type_error(self, runner):
        with pytest.raises(TypeError):
            runner.run("ping", 12345)

    @pytest.mark.runner
    @pytest.mark.network
    def test_ping_dispatch_returns_test_result(self, runner):
        result = runner.run("ping", "127.0.0.1", timeout=1, count=1)

        assert isinstance(result, TestResult)
        assert result.status == "PASS"
        assert result.duration_ms >= 0
        assert isinstance(result.metadata, dict)
        assert result.metadata["is_reachable"] is True

    @pytest.mark.runner
    @pytest.mark.network
    def test_tcp_dispatch_success(self, runner, mock_tcp_server: Tuple[str, int]):
        host, port = mock_tcp_server
        result = runner.run("tcp", f"{host}:{port}", timeout=2.0)

        assert isinstance(result, TestResult)
        assert result.status == "PASS"
        assert result.target == f"{host}:{port}"
        assert result.duration_ms >= 0
        assert isinstance(result.metadata, dict)
        assert result.metadata["is_connected"] is True

    @pytest.mark.runner
    @pytest.mark.network
    def test_tcp_dispatch_failure(self, runner, closed_port: Tuple[str, int]):
        host, port = closed_port
        result = runner.run("tcp", f"{host}:{port}", timeout=1.0)

        assert isinstance(result, TestResult)
        assert result.status == "FAIL"
        assert result.duration_ms >= 0
        assert result.metadata["is_connected"] is False

    @pytest.mark.runner
    @pytest.mark.network
    def test_port_dispatch_open(self, runner, mock_tcp_server: Tuple[str, int]):
        host, port = mock_tcp_server
        result = runner.run("port", f"{host}:{port}", timeout=2.0)

        assert isinstance(result, TestResult)
        assert result.status == "PASS"
        assert result.metadata["state"] == "OPEN"

    @pytest.mark.runner
    @pytest.mark.network
    def test_udp_dispatch_echo(self, runner, udp_server: Tuple[str, int]):
        host, port = udp_server
        result = runner.run("udp", f"{host}:{port}", timeout=1.0)

        assert isinstance(result, TestResult)
        assert result.status == "PASS"
        assert result.latency_ms is not None
        assert result.duration_ms >= 0
        assert result.metadata["received"] == 1

    @pytest.mark.runner
    @pytest.mark.network
    def test_udp_dispatch_requires_port(self, runner):
        with pytest.raises(ValueError, match="port"):
            runner.run("udp", "127.0.0.1")

    @pytest.mark.runner
    @pytest.mark.network
    def test_invalid_target_port_raises_value_error(self, runner):
        with pytest.raises(ValueError):
            runner.run("tcp", "example.com:99999")