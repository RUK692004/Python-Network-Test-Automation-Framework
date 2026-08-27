"""
Target configuration management for Network Test Automation Framework.

Supports loading test target options from environment variables or python defaults.
Designed to be easily extended with YAML configuration in Phase 4.
"""

from dataclasses import dataclass
import os


@dataclass
class TestConfig:
    """
    Data class representing network test target configuration.

    Attributes:
        host: Target IP address or hostname.
        port: Target TCP port number.
        ping_timeout: Timeout in seconds for ICMP ping checks.
        tcp_timeout: Timeout in seconds for TCP socket connection attempts.
    """

    host: str = "127.0.0.1"
    port: int = 8080
    ping_timeout: int = 2
    tcp_timeout: float = 3.0

    @classmethod
    def from_env(cls) -> "TestConfig":
        """
        Load configuration settings from environment variables with fallback defaults.

        Returns:
            TestConfig: Populated configuration instance.
        """
        host = os.getenv("TARGET_HOST", "127.0.0.1")

        try:
            port = int(os.getenv("TARGET_PORT", "8080"))
        except ValueError:
            port = 8080

        try:
            ping_timeout = int(os.getenv("PING_TIMEOUT", "2"))
        except ValueError:
            ping_timeout = 2

        try:
            tcp_timeout = float(os.getenv("TCP_TIMEOUT", "3.0"))
        except ValueError:
            tcp_timeout = 3.0

        return cls(
            host=host,
            port=port,
            ping_timeout=ping_timeout,
            tcp_timeout=tcp_timeout,
        )


# Note for Phase 4 Extension:
# YAML configuration loader (e.g. from_yaml(filepath)) will be added here
# without breaking existing tests relying on TestConfig.

DEFAULT_CONFIG = TestConfig.from_env()
