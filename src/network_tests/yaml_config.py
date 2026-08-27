"""
YAML configuration loader for Network Test Automation Framework.

Loads and validates the performance configuration from
``config/performance_config.yaml``. Falls back to sensible defaults when
values are missing and rejects invalid values with clear errors.

This supports Phase 3 performance thresholds and will later back the
full Phase 4 YAML configuration system.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from utils.logger import get_logger

logger = get_logger("network_tests.yaml_config")

DEFAULT_CONFIG: Dict[str, Any] = {
    "target": {"host": "127.0.0.1"},
    "performance": {
        "throughput": {
            "enabled": True,
            "duration_seconds": 2.0,
            "buffer_size": 65536,
            "data_chunk_bytes": 65536,
            "port": 5001,
        },
        "udp_throughput": {
            "enabled": True,
            "packet_count": 100,
            "payload_size": 1024,
            "port": 5002,
        },
        "latency": {"samples": 20},
        "packet_loss": {"samples": 20},
    },
    "thresholds": {
        "throughput": {"min_mbps": 0.0},
        "latency": {"max_average_ms": 100, "max_p95_ms": 150},
        "packet_loss": {"max_percent": 5.0},
    },
}


@dataclass
class ThroughputConfig:
    """TCP throughput test configuration."""

    enabled: bool = True
    duration_seconds: float = 2.0
    buffer_size: int = 65536
    data_chunk_bytes: int = 65536
    port: int = 5001


@dataclass
class UdpThroughputConfig:
    """UDP throughput test configuration."""

    enabled: bool = True
    packet_count: int = 100
    payload_size: int = 1024
    port: int = 5002


@dataclass
class LatencyConfig:
    """Latency measurement configuration."""

    samples: int = 20


@dataclass
class PacketLossConfig:
    """Packet-loss measurement configuration."""

    samples: int = 20


@dataclass
class PerformanceConfig:
    """Aggregated performance-test configuration."""

    throughput: ThroughputConfig = field(default_factory=ThroughputConfig)
    udp_throughput: UdpThroughputConfig = field(default_factory=UdpThroughputConfig)
    latency: LatencyConfig = field(default_factory=LatencyConfig)
    packet_loss: PacketLossConfig = field(default_factory=PacketLossConfig)


@dataclass
class ThresholdConfig:
    """Performance threshold configuration."""

    min_throughput_mbps: float = 0.0
    max_average_latency_ms: float = 100
    max_p95_latency_ms: float = 150
    max_packet_loss_percent: float = 5.0


@dataclass
class AppConfig:
    """Top-level application configuration loaded from YAML."""

    host: str = "127.0.0.1"
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)


def _require_yaml():
    """Import yaml lazily so missing PyYAML produces a clear error."""
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "PyYAML is required to load performance configuration. "
            "Install it with: pip install PyYAML"
        ) from exc
    return yaml


def _safe_float(value: Any, default: float) -> float:
    """Convert a YAML value to float, returning default on failure."""
    try:
        result = float(value)
        if result != result:  # NaN check
            return default
        return result
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int) -> int:
    """Convert a YAML value to int, returning default on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any, default: bool) -> bool:
    """Convert a YAML value to bool, returning default on failure."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes")
    return default


def _validate_positive_float(value: Any, default: float) -> float:
    """Validate a float is positive, returning default if invalid."""
    result = _safe_float(value, default)
    if result <= 0:
        logger.warning(
            f"Non-positive float ({value!r}); using default {default}"
        )
        return default
    return result


def _validate_positive_int(value: Any, default: int) -> int:
    """Validate an int is positive, returning default if invalid."""
    result = _safe_int(value, default)
    if result <= 0:
        logger.warning(
            f"Non-positive integer ({value!r}); using default {default}"
        )
        return default
    return result


def _validate_port(value: Any, default: int) -> int:
    """Validate an int is a valid TCP/UDP port (1-65535)."""
    result = _safe_int(value, default)
    if not (1 <= result <= 65535):
        logger.warning(
            f"Port out of range ({value!r}); using default {default}"
        )
        return default
    return result


def load_performance_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Load performance configuration from a YAML file.

    Args:
        config_path: Optional path to a YAML config file. If None, the
            default ``config/performance_config.yaml`` is used.

    Returns:
        AppConfig populated with values from the YAML file, falling back
        to defaults for any missing or invalid entries.

    Raises:
        ImportError: If PyYAML is not installed.
        FileNotFoundError: If the config file does not exist.
    """
    yaml = _require_yaml()

    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config",
            "performance_config.yaml",
        )
        config_path = os.path.normpath(config_path)

    logger.debug(f"Loading performance configuration from {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return _parse_config(raw)


def _parse_config(raw: Dict[str, Any]) -> AppConfig:
    """Parse a raw YAML dict into an AppConfig with validation."""
    target = raw.get("target", {}) or {}
    perf_raw = raw.get("performance", {}) or {}
    thresh_raw = raw.get("thresholds", {}) or {}

    host = target.get("host", DEFAULT_CONFIG["target"]["host"])
    if not isinstance(host, str) or not host.strip():
        host = DEFAULT_CONFIG["target"]["host"]

    tp_cfg = perf_raw.get("throughput", {}) or {}
    udp_tp_cfg = perf_raw.get("udp_throughput", {}) or {}
    lat_cfg = perf_raw.get("latency", {}) or {}
    loss_cfg = perf_raw.get("packet_loss", {}) or {}

    performance = PerformanceConfig(
        throughput=ThroughputConfig(
            enabled=_safe_bool(tp_cfg.get("enabled", True), True),
            duration_seconds=_validate_positive_float(
                tp_cfg.get("duration_seconds", 2.0), default=2.0
            ),
            buffer_size=_validate_positive_int(
                tp_cfg.get("buffer_size", 65536), default=65536
            ),
            data_chunk_bytes=_validate_positive_int(
                tp_cfg.get("data_chunk_bytes", 65536), default=65536
            ),
            port=_validate_port(tp_cfg.get("port", 5001), default=5001),
        ),
        udp_throughput=UdpThroughputConfig(
            enabled=_safe_bool(udp_tp_cfg.get("enabled", True), True),
            packet_count=_validate_positive_int(
                udp_tp_cfg.get("packet_count", 100), default=100
            ),
            payload_size=_validate_positive_int(
                udp_tp_cfg.get("payload_size", 1024), default=1024
            ),
            port=_validate_port(udp_tp_cfg.get("port", 5002), default=5002),
        ),
        latency=LatencyConfig(
            samples=_validate_positive_int(lat_cfg.get("samples", 20), default=20)
        ),
        packet_loss=PacketLossConfig(
            samples=_validate_positive_int(
                loss_cfg.get("samples", 20), default=20
            )
        ),
    )

    tp_thresh = thresh_raw.get("throughput", {}) or {}
    lat_thresh = thresh_raw.get("latency", {}) or {}
    loss_thresh = thresh_raw.get("packet_loss", {}) or {}

    thresholds = ThresholdConfig(
        min_throughput_mbps=_safe_float(tp_thresh.get("min_mbps", 0.0), 0.0),
        max_average_latency_ms=_safe_float(
            lat_thresh.get("max_average_ms", 100), 100
        ),
        max_p95_latency_ms=_safe_float(
            lat_thresh.get("max_p95_ms", 150), 150
        ),
        max_packet_loss_percent=_safe_float(
            loss_thresh.get("max_percent", 5.0), 5.0
        ),
    )

    logger.info(
        f"Configuration loaded: host={host}, performance/thresholds parsed"
    )
    return AppConfig(host=host, performance=performance, thresholds=thresholds)
