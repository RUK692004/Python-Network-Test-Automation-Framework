"""
Target representation for the Network Diagnostics Engine.

This module provides a single, reusable abstraction for network test targets.
It centralizes target parsing so that the rest of the framework (runner,
individual test modules, API layer) never has to duplicate the same parsing
logic, and so that all tests agree on how a target is identified.

A target is represented as a `host` plus an optional `port`, optionally with
an implied `protocol`.  This covers the common forms:

    google.com
    192.168.1.10
    example.com:443
    192.168.1.10:8080
    8.8.8.8/udp

The module does *not* perform DNS lookups or network I/O – it only parses and
serialises target strings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, order=True)
class Target:
    """
    Immutable representation of a network test target.

    Attributes:
        host: IP address or hostname.  Always non-empty, whitespace-stripped.
        port: Optional TCP/UDP port.  `None` when the target does not specify
            one (ICMP such as ping may not use a port).
        protocol: Implied protocol for the test.  Defaults to "tcp" for a
            host:port target.  When the target string includes a scheme-like
            suffix (e.g. "/udp") the protocol is recorded here.
    """

    host: str
    port: Optional[int] = None
    protocol: str = "tcp"

    # ---------------------------------------------------------------------------
    # Construction helpers
    # ---------------------------------------------------------------------------

    @classmethod
    def from_string(cls, target_str: str) -> "Target":
        """
        Parse a target string into a `Target` instance.

        Supported forms:
            "host"               -> host only, port=None
            "host:port"          -> host + port, protocol="tcp"
            "host/udp"           -> host only, protocol="udp"
            "host:port/udp"      -> host + port, protocol="udp"
            "host/protocol"      -> host only, protocol=<custom>

        The method does not perform DNS resolution; it simply validates the
        shape of the string and splits it.

        Args:
            target_str: Raw target string.

        Returns:
            A `Target` instance.

        Raises:
            ValueError: If the string is empty or contains an invalid port.
        """
        if not target_str or not isinstance(target_str, str):
            raise ValueError("Target string must be a non-empty string.")

        clean = target_str.strip()
        if not clean:
            raise ValueError("Target string is empty after stripping whitespace.")

        # Split off optional protocol suffix (e.g. "/udp", "/icmp")
        protocol = "tcp"
        if "/" in clean:
            host_part, _, proto_part = clean.partition("/")
            proto_part = proto_part.strip().lower()
            if proto_part:
                protocol = proto_part

        # Split host and port
        host = clean
        port = None
        if ":" in host_part:
            host_part, _, port_part = host_part.rpartition(":")
            host = host_part.strip()
            port_part = port_part.strip()
            if port_part:
                try:
                    port = int(port_part)
                except ValueError:
                    raise ValueError(
                        f"Invalid port '{port_part}' in target '{target_str}'."
                    ) from None
                if not (1 <= port <= 65535):
                    raise ValueError(
                        f"Port {port} out of range 1-65535 in target '{target_str}'."
                    )

        if not host:
            raise ValueError(f"Host component is empty in target '{target_str}'.")

        return cls(host=host, port=port, protocol=protocol)

    # ---------------------------------------------------------------------------
    # Serialisation helpers
    # ---------------------------------------------------------------------------

    def to_string(self, include_port: bool = True) -> str:
        """
        Return the target as a compact string.

        Args:
            include_port: When `True` and a port is set, append ":port".

        Returns:
            A string such as "google.com" or "example.com:443".
        """
        if self.port is not None and include_port:
            return f"{self.host}:{self.port}"
        return self.host

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        port = f", port={self.port}" if self.port is not None else ""
        return f"<Target host={self.host!r}, port={port}, protocol={self.protocol!r}>"

    # ---------------------------------------------------------------------------
    # Validation helpers (reused by test modules)
    # ---------------------------------------------------------------------------

    @classmethod
    def validate_host(cls, host: str) -> Optional[str]:
        """
        Validate a host string; return an error message or `None`.

        Reused by test modules (`ping`, `tcp`, `port`, `udp`) to centralise
        the common host-validation logic that used to be duplicated.
        """
        if not isinstance(host, str) or not host.strip():
            return "Invalid target host provided"
        return None

    @classmethod
    def validate_port(cls, port: int) -> Optional[str]:
        """
        Validate a port integer; return an error message or `None`.
        """
        if not isinstance(port, int) or not (1 <= port <= 65535):
            return f"Invalid port number: {port}. Port must be between 1 and 65535."
        return None
