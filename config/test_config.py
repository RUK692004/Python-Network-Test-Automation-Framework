"""
Centralized project target configuration defaults.

This file serves as a simple configuration module for Phase 1.
Phase 4 will introduce test_config.yaml in this directory.
"""

from network_tests.config import TestConfig

# Default target parameters
HOST = "127.0.0.1"
PORT = 8080
PING_TIMEOUT = 2
TCP_TIMEOUT = 3.0

# Pre-built active configuration
active_config = TestConfig(
    host=HOST,
    port=PORT,
    ping_timeout=PING_TIMEOUT,
    tcp_timeout=TCP_TIMEOUT,
)
