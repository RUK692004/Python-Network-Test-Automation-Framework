"""
Package initialization for network_tests module.
"""

from network_tests.config import TestConfig, DEFAULT_CONFIG
from network_tests.udp import UDPResult, udp_send, udp_send_receive
from network_tests.metrics import (
    LatencyStats,
    calculate_latency_stats,
    measure_udp_latency,
    packet_loss_percentage,
)

__all__ = [
    "TestConfig",
    "DEFAULT_CONFIG",
    "UDPResult",
    "udp_send",
    "udp_send_receive",
    "LatencyStats",
    "calculate_latency_stats",
    "measure_udp_latency",
    "packet_loss_percentage",
]
