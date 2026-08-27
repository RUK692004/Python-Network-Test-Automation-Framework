"""
Automated pytest suite for TCP socket connectivity tests.
"""

from typing import Tuple

import pytest

# Import the module rather than `test_tcp_connection` by name so pytest does
# not treat the imported function as a phantom test case (fixture 'host').
from network_tests import tcp as tcp_module
from network_tests.tcp import TCPResult


@pytest.mark.tcp
@pytest.mark.network
def test_tcp_connection_success(mock_tcp_server: Tuple[str, int]):
    """
    Verify TCP connection test returns PASS when connecting to an active listening port.
    """
    host, port = mock_tcp_server
    result = tcp_module.test_tcp_connection(host=host, port=port, timeout=2.0)

    assert isinstance(result, TCPResult)
    assert result.is_connected is True
    assert result.status == "PASS"
    assert result.message == "TCP connection established"
    assert result.target == host
    assert result.port == port


@pytest.mark.tcp
@pytest.mark.network
def test_tcp_connection_refused(closed_port: Tuple[str, int]):
    """
    Verify TCP connection test returns FAIL with ConnectionRefusedError status on closed port.
    """
    host, port = closed_port
    result = tcp_module.test_tcp_connection(host=host, port=port, timeout=1.0)

    assert isinstance(result, TCPResult)
    assert result.is_connected is False
    assert result.status == "FAIL"
    # Closing a port should surface as a graceful failure, not an unhandled
    # exception. Linux/WSL surfaces it as ConnectionRefusedError, whereas
    # Windows loopback may surface WSAEWOULDBLOCK as a socket.timeout instead.
    assert result.error_type in {"ConnectionRefusedError", "socket.timeout"}
    assert "refused" in result.message or "timed out" in result.message


@pytest.mark.tcp
@pytest.mark.network
def test_tcp_invalid_hostname():
    """
    Verify TCP connection test handles DNS resolution failure gracefully.
    """
    invalid_host = "invalid.hostname.test.nonexistent"
    result = tcp_module.test_tcp_connection(host=invalid_host, port=80, timeout=1.0)

    assert isinstance(result, TCPResult)
    assert result.is_connected is False
    assert result.status == "FAIL"
    assert result.error_type == "socket.gaierror"


@pytest.mark.tcp
@pytest.mark.network
def test_tcp_invalid_port():
    """
    Verify TCP connection test rejects invalid port range values cleanly.
    """
    invalid_port = 999999
    result = tcp_module.test_tcp_connection(host="127.0.0.1", port=invalid_port, timeout=1.0)

    assert isinstance(result, TCPResult)
    assert result.is_connected is False
    assert result.status == "FAIL"
    assert "Invalid port" in result.message
