"""
Target configuration management for Network Test Automation Framework.

Supports loading test target options from environment variables or python defaults.
Designed to be easily extended with YAML configuration in Phase 4.
"""

from dataclasses import dataclass
import os

from utils.logger import get_logger

logger = get_logger("network_tests.config")

# ---------------------------------------------------------------------------
# Fallback defaults used whenever an environment variable is missing or invalid.
# TARGET_HOST / TARGET_PORT / PING_TIMEOUT / TCP_TIMEOUT override these.
# ---------------------------------------------------------------------------
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
DEFAULT_PING_TIMEOUT = 2
DEFAULT_TCP_TIMEOUT = 3.0

PORT_MIN = 1
PORT_MAX = 65535


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

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    ping_timeout: int = DEFAULT_PING_TIMEOUT
    tcp_timeout: float = DEFAULT_TCP_TIMEOUT

    @classmethod
    def from_env(cls) -> "TestConfig":
        """
        Load configuration from environment variables with sensibly validated defaults.

        The following environment variables are supported, matching the
        PowerShell export syntax `$env:TARGET_HOST=...` etc.:

            TARGET_HOST  (default 127.0.0.1)
            TARGET_PORT  (default 8080)
            PING_TIMEOUT (default 2)
            TCP_TIMEOUT  (default 3.0)

        Any missing, empty, or invalid value falls back to its default and is
        reported via the centralized logger instead of raising.

        Returns:
            TestConfig: Populated configuration instance.
        """
        host = cls._load_host("TARGET_HOST", DEFAULT_HOST)
        port = cls._load_port("TARGET_PORT", DEFAULT_PORT)
        ping_timeout = cls._load_timeout(
            "PING_TIMEOUT", DEFAULT_PING_TIMEOUT, integer=True
        )
        tcp_timeout = cls._load_timeout(
            "TCP_TIMEOUT", DEFAULT_TCP_TIMEOUT, integer=False
        )

        return cls(
            host=host,
            port=port,
            ping_timeout=ping_timeout,
            tcp_timeout=tcp_timeout,
        )

    @staticmethod
    def _load_host(name: str, default: str) -> str:
        """Load a non-empty host value, falling back to ``default`` if unset/blank."""
        raw = os.getenv(name)
        if raw is None:
            return default
        if not raw.strip():
            logger.warning(
                f"Environment variable '{name}' is empty; using default host '{default}'."
            )
            return default
        return raw.strip()

    @staticmethod
    def _load_port(name: str, default: int) -> int:
        """Load a port integer in range 1-65535, falling back to ``default`` when invalid."""
        raw = os.getenv(name)
        if raw is None:
            return default
        try:
            value = int(raw)
        except ValueError:
            logger.warning(
                f"Environment variable '{name}' is not an integer ('{raw}'); "
                f"using default port {default}."
            )
            return default
        if not (PORT_MIN <= value <= PORT_MAX):
            logger.warning(
                f"Environment variable '{name}' is out of range ({value}). "
                f"Port must be between {PORT_MIN} and {PORT_MAX}; "
                f"using default port {default}."
            )
            return default
        return value

    @staticmethod
    def _load_timeout(name: str, default: float, integer: bool) -> float:
        """Load a positive timeout (int or float), falling back to ``default`` when invalid."""
        raw = os.getenv(name)
        if raw is None:
            return default
        try:
            value = int(raw) if integer else float(raw)
        except ValueError:
            logger.warning(
                f"Environment variable '{name}' is not a valid number ('{raw}'). "
                f"Using default timeout {default}s."
            )
            return default
        if value <= 0:
            logger.warning(
                f"Environment variable '{name}' must be positive (got {value}). "
                f"Using default timeout {default}s."
            )
            return default
        return value


# Note for Phase 4 Extension:
# YAML configuration loader (e.g. from_yaml(filepath)) will be added here
# without breaking existing tests relying on TestConfig.

DEFAULT_CONFIG = TestConfig.from_env()
