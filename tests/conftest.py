"""
Pytest configuration and shared fixtures for Network Test Automation Framework.

Provides configurable target fixtures and a local TCP echo server fixture
to enable deterministic, offline-capable test execution.
"""

import socket
import threading
from typing import Generator, Tuple

import pytest
from network_tests.config import TestConfig, DEFAULT_CONFIG


@pytest.fixture
def target_config() -> TestConfig:
    """
    Fixture providing test target configuration parameters.

    Returns:
        TestConfig instance configured from environment or defaults.
    """
    return DEFAULT_CONFIG


@pytest.fixture
def mock_tcp_server() -> Generator[Tuple[str, int], None, None]:
    """
    Fixture that spins up a temporary background TCP server on localhost.

    Yields:
        Tuple[str, int]: (host, port) of the listening socket.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("127.0.0.1", 0))  # OS assigns an available port
    server_socket.listen(5)
    host, port = server_socket.getsockname()

    stop_event = threading.Event()

    def run_server():
        server_socket.settimeout(0.5)
        while not stop_event.is_set():
            try:
                conn, _ = server_socket.accept()
                conn.close()
            except socket.timeout:
                continue
            except OSError:
                break

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    yield host, port

    stop_event.set()
    thread.join(timeout=1.0)
    try:
        server_socket.close()
    except OSError:
        pass


@pytest.fixture
def closed_port() -> Tuple[str, int]:
    """
    Fixture providing a localhost host and port guaranteed to be closed/refused.

    Returns:
        Tuple[str, int]: (host, port) where no listener is active.
    """
    temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    temp_sock.bind(("127.0.0.1", 0))
    _, port = temp_sock.getsockname()
    temp_sock.close()  # Close immediately so port is free but not listening
    return "127.0.0.1", port
