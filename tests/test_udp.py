"""
Automated pytest suite for UDP communication tests.
"""

import socket
from typing import Tuple

import pytest

from network_tests.udp import udp_send, udp_send_receive, UDPResult


@pytest.mark.udp
@pytest.mark.network
def test_udp_send_to_valid_target(udp_server: Tuple[str, int]):
    """
    Verify a UDP datagram can be sent to a valid local endpoint.
    """
    host, port = udp_server
    result = udp_send(host=host, port=port, data=b"hello udp", timeout=1.0)

    assert isinstance(result, UDPResult)
    assert result.success is True
    assert result.sent == 1


@pytest.mark.udp
@pytest.mark.network
def test_udp_send_receive_echo(udp_server: Tuple[str, int]):
    """
    Verify UDP communication works when a UDP echo endpoint is available,
    and that a latency value is measured.
    """
    host, port = udp_server
    result = udp_send_receive(host=host, port=port, data=b"ping-udp", timeout=1.0)

    assert isinstance(result, UDPResult)
    assert result.success is True
    assert result.received == 1
    assert result.latency_ms is not None
    assert result.latency_ms >= 0.0
    assert "response" in result.message.lower()


@pytest.mark.udp
@pytest.mark.network
def test_udp_multiple_packets(udp_server: Tuple[str, int]):
    """
    Verify multiple UDP packets can be transmitted and acknowledged successfully.
    """
    host, port = udp_server
    successful = 0
    for index in range(1, 6):
        result = udp_send_receive(
            host=host, port=port, data=f"packet-{index}".encode(), timeout=1.0
        )
        if result.success:
            successful += 1

    assert successful == 5


@pytest.mark.udp
@pytest.mark.network
def test_udp_invalid_hostname():
    """
    Verify UDP send fails cleanly (gaierror) for an unresolvable hostname.
    """
    result = udp_send_receive(
        host="invalid.hostname.test.nonexistent", port=5000, timeout=1.0
    )

    assert isinstance(result, UDPResult)
    assert result.success is False
    assert result.error_type == "socket.gaierror"


@pytest.mark.udp
@pytest.mark.network
def test_udp_empty_host():
    """
    Verify UDP send fails cleanly for a blank/empty host.
    """
    result = udp_send_receive(host="   ", port=5000, timeout=1.0)

    assert isinstance(result, UDPResult)
    assert result.success is False
    assert result.error_type == "ValueError"
    assert "host" in result.message.lower()


@pytest.mark.udp
@pytest.mark.network
@pytest.mark.parametrize("invalid_port", [0, -1, 65536, 999999])
def test_udp_invalid_port(invalid_port: int):
    """
    Verify UDP send rejects invalid port values cleanly (parameterized).
    """
    result = udp_send_receive(host="127.0.0.1", port=invalid_port, timeout=1.0)

    assert isinstance(result, UDPResult)
    assert result.success is False
    assert result.error_type == "ValueError"
    assert "Invalid port" in result.message
    assert "between 1 and 65535" in result.message


@pytest.mark.udp
@pytest.mark.network
def test_udp_no_response_closed_port():
    """
    Verify UDP send/receive fails cleanly when no endpoint responds on a closed port.

    On Windows, a closed localhost UDP port surfaces an immediate connection
    reset (WSAECONNRESET); on Linux it typically times out. Both are valid
    "no UDP response" outcomes that the framework must classify gracefully.
    """
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    probe.bind(("127.0.0.1", 0))
    _, port = probe.getsockname()
    probe.close()

    result = udp_send_receive(host="127.0.0.1", port=port, data=b"x", timeout=0.3)

    assert isinstance(result, UDPResult)
    assert result.success is False
    assert result.error_type in {"socket.timeout", "ConnectionResetError"}


@pytest.mark.udp
@pytest.mark.network
def test_udp_timeout_branch(monkeypatch):
    """
    Verify UDP send/receive maps a response timeout into a socket.timeout result.

    The timeout branch is forced deterministically by making the socket's
    recvfrom raise socket.timeout, independently of how the host OS surfaces
    a missing response.
    """
    def always_timeout(self, *args, **kwargs):
        raise socket.timeout("timed out")

    monkeypatch.setattr(socket.socket, "recvfrom", always_timeout)

    result = udp_send_receive(host="127.0.0.1", port=5000, data=b"x", timeout=0.1)

    assert isinstance(result, UDPResult)
    assert result.success is False
    assert result.error_type == "socket.timeout"
    assert "timeout" in result.message.lower()

