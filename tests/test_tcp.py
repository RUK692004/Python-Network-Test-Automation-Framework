"""
Automated pytest suite for TCP socket connectivity tests.
"""

from typing import Tuple

import pytest
import socket

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
def test_tcp_connection_refused(monkeypatch):
    """
    Verify the framework maps a refused TCP connection into a FAIL result.

    A *genuine* ConnectionRefusedError cannot be produced reliably by connecting
    to a closed local port: on Windows (and some sandboxes) the OS reports
    WSAEWOULDBLOCK, which Python surfaces as socket.timeout rather than raising
    WSAECONNREFUSED / ECONNREFUSED. To test the framework's refusal-handling
    branch deterministically on every platform, we raise the exact socket error
    at the connect boundary and assert the framework's translation of it.

    Network result = CONNECTION_REFUSED  ->  pytest result = PASS
    (the framework correctly reported the expected condition).
    """

    def refused_connect(self, address):
        raise ConnectionRefusedError("[Errno 111] Connection refused")

    # Patch only the connect step; the rest of the real socket flow is untouched.
    monkeypatch.setattr(socket.socket, "connect", refused_connect)

    result = tcp_module.test_tcp_connection(host="127.0.0.1", port=80, timeout=1.0)

    assert isinstance(result, TCPResult)
    assert result.is_connected is False
    assert result.status == "FAIL"
    assert result.error_type == "ConnectionRefusedError"
    assert result.message == "Connection refused"


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
    assert "between 1 and 65535" in result.message
