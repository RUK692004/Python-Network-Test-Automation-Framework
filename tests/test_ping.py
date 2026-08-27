"""
Automated pytest suite for ICMP Ping connectivity tests.
"""

import pytest

# Aliased so the dataclass name does not start with "Test" (pytest would
# otherwise try to collect TestConfig as a test class and raise a warning).
from network_tests.config import TestConfig as TargetsConfig
from network_tests.ping import ping_target, PingResult


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

    assert isinstance(result, PingResult)
    assert result.is_reachable is True
    assert result.status == "PASS"
    assert result.message == "Host is reachable"
    assert result.target == target_config.host


@pytest.mark.ping
@pytest.mark.network
def test_ping_unreachable_host():
    """
    Verify ping test gracefully returns FAIL status for invalid/unreachable target without throwing exceptions.
    """
    # 192.0.2.1 is reserved for documentation (TEST-NET-1) and non-routable
    unreachable_ip = "192.0.2.1"
    result = ping_target(host=unreachable_ip, timeout=1, count=1)

    assert isinstance(result, PingResult)
    assert result.is_reachable is False
    assert result.status == "FAIL"
    assert "unreachable" in result.message.lower() or "timed out" in result.message.lower()
