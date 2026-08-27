"""
Automated pytest suite for TCP Port Availability tests.
"""

from typing import Tuple
import pytest

from network_tests.port import check_port_availability, PortStatusResult


@pytest.mark.port
@pytest.mark.network
def test_port_availability_open(mock_tcp_server: Tuple[str, int]):
    """
    Verify port availability test detects OPEN port correctly on active listening socket.
    """
    host, port = mock_tcp_server
    result = check_port_availability(host=host, port=port, timeout=2.0)

    assert isinstance(result, PortStatusResult)
    assert result.is_open is True
    assert result.state == "OPEN"
    assert "OPEN" in result.message
    assert result.target == host
    assert result.port == port


@pytest.mark.port
@pytest.mark.network
def test_port_availability_closed(closed_port: Tuple[str, int]):
    """
    Verify port availability test detects CLOSED port when connection is refused.
    """
    host, port = closed_port
    result = check_port_availability(host=host, port=port, timeout=1.0)

    assert isinstance(result, PortStatusResult)
    assert result.is_open is False
    assert result.state == "CLOSED"
    assert "CLOSED" in result.message


@pytest.mark.port
@pytest.mark.network
def test_port_availability_invalid_host():
    """
    Verify port availability test reports INVALID_HOST status on DNS resolution failure.
    """
    invalid_host = "invalid.hostname.test.nonexistent"
    result = check_port_availability(host=invalid_host, port=80, timeout=1.0)

    assert isinstance(result, PortStatusResult)
    assert result.is_open is False
    assert result.state == "INVALID_HOST"
