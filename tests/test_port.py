"""
Automated pytest suite for TCP Port Availability tests.
"""

from typing import Tuple
import pytest

from network_tests.port import check_port_availability
from network_tests.results import TestResult


@pytest.mark.port
@pytest.mark.network
def test_port_availability_open(mock_tcp_server: Tuple[str, int]):
    """
    Verify port availability test detects OPEN port correctly on active listening socket.
    """
    host, port = mock_tcp_server
    result = check_port_availability(host=host, port=port, timeout=2.0)

    assert isinstance(result, TestResult)
    assert result.is_success is True
    assert result.status == "PASS"
    assert result.error is None
    assert result.target == f"{host}:{port}"
    assert result.duration_ms >= 0
    assert isinstance(result.metadata, dict)
    assert result.metadata["is_open"] is True
    assert result.metadata["state"] == "OPEN"
    assert "OPEN" in result.metadata["message"]
    assert result.metadata["port"] == port


@pytest.mark.port
@pytest.mark.network
def test_port_availability_closed(closed_port: Tuple[str, int]):
    """
    Verify port availability test detects CLOSED port when connection is refused.
    """
    host, port = closed_port
    result = check_port_availability(host=host, port=port, timeout=1.0)

    assert isinstance(result, TestResult)
    assert result.is_success is False
    assert result.status == "FAIL"
    assert result.duration_ms >= 0
    assert result.metadata["is_open"] is False
    assert result.metadata["state"] == "CLOSED"
    assert "CLOSED" in result.error


@pytest.mark.port
@pytest.mark.network
def test_port_availability_invalid_host():
    """
    Verify port availability test reports INVALID_HOST status on DNS resolution failure.
    """
    invalid_host = "invalid.hostname.test.nonexistent"
    result = check_port_availability(host=invalid_host, port=80, timeout=1.0)

    assert isinstance(result, TestResult)
    assert result.is_success is False
    assert result.status == "FAIL"
    assert result.metadata["is_open"] is False
    assert result.metadata["state"] == "INVALID_HOST"
