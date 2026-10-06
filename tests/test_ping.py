"""
Automated pytest suite for ICMP Ping connectivity tests.
"""

import pytest

# Aliased so the dataclass name does not start with "Test" (pytest would
# otherwise try to collect TestConfig as a test class and raise a warning).
from network_tests.config import TestConfig as TargetsConfig
from network_tests.ping import ping_target
from network_tests.results import TestResult


@pytest.mark.ping
@pytest.mark.network
def test_ping_reachable_host(target_config: TargetsConfig):
    """
    Verify ping test successfully reports PASS when target host (127.0.0.1) is reachable.
    """
    result = ping_target(
        host=target_config.host,
        timeout=target_config.ping_timeout,
        count=1,
    )

    assert isinstance(result, TestResult)
    assert result.is_success is True
    assert result.status == "PASS"
    assert result.error is None
    assert result.target == target_config.host
    assert result.duration_ms >= 0
    assert isinstance(result.metadata, dict)
    assert result.metadata["is_reachable"] is True


@pytest.mark.ping
@pytest.mark.network
def test_ping_unreachable_host():
    """
    Verify ping test gracefully returns FAIL status for invalid/unreachable target without throwing exceptions.
    """
    # 192.0.2.1 is reserved for documentation (TEST-NET-1) and non-routable
    unreachable_ip = "192.0.2.1"
    result = ping_target(host=unreachable_ip, timeout=1, count=1)

    assert isinstance(result, TestResult)
    assert result.is_success is False
    assert result.status == "FAIL"
    assert result.target == unreachable_ip
    assert result.duration_ms >= 0
    error = (result.error or "").lower()
    assert "unreachable" in error or "timed out" in error
    assert result.metadata["is_reachable"] is False


@pytest.mark.ping
@pytest.mark.network
def test_ping_invalid_host_returns_failure_result():
    """
    Verify a blank host yields a structured FAIL TestResult instead of raising.
    """
    result = ping_target(host="", timeout=1, count=1)

    assert isinstance(result, TestResult)
    assert result.is_success is False
    assert result.status == "FAIL"
    assert "Invalid target host" in (result.error or "")
