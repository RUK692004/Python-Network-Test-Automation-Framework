"""
Tests for network_tests.yaml_config (Phase 3 performance configuration).

Validates YAML loading, defaults, and rejection of invalid values.
"""

import os

import pytest

yaml = pytest.importorskip("yaml")

from network_tests.yaml_config import (
    AppConfig,
    DEFAULT_CONFIG,
    load_performance_config,
)


def _write(tmp_path, content):
    path = tmp_path / "perf.yaml"
    path.write_text(content, encoding="utf-8")
    return str(path)


@pytest.mark.performance
class TestLoadDefaultConfig:
    """Loading the shipped config/performance_config.yaml."""

    def test_shipped_yaml_loads(self):
        app = load_performance_config()
        assert isinstance(app, AppConfig)
        assert app.host

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_performance_config(os.path.join("nonexistent", "cfg.yaml"))


@pytest.mark.performance
class TestParseConfig:
    """Direct _parse_config-style validation via load_performance_config."""

    def test_valid_values_are_used(self, tmp_path):
        cfg = """
target:
  host: "192.168.1.10"
performance:
  throughput:
    duration_seconds: 5.0
    buffer_size: 32768
    port: 6001
  latency:
    samples: 40
thresholds:
  throughput:
    min_mbps: 75
  latency:
    max_average_ms: 60
thresholds_packet_loss_marker: true
"""
        app = load_performance_config(_write(tmp_path, cfg))
        assert app.host == "192.168.1.10"
        assert app.performance.throughput.duration_seconds == 5.0
        assert app.performance.throughput.buffer_size == 32768
        assert app.performance.throughput.port == 6001
        assert app.performance.latency.samples == 40
        assert app.thresholds.min_throughput_mbps == 75.0
        assert app.thresholds.max_average_latency_ms == 60.0

    def test_empty_document_uses_defaults(self, tmp_path):
        app = load_performance_config(_write(tmp_path, ""))
        assert app.host == DEFAULT_CONFIG["target"]["host"]
        assert app.performance.latency.samples == 20
        assert app.thresholds.max_p95_latency_ms == 150.0


@pytest.mark.performance
class TestInvalidConfigValues:
    """Invalid values must be rejected/ defaulted clearly, never accepted silently."""

    @pytest.mark.parametrize(
        "key_path,bad",
        [
            ("duration_seconds", -1),
            ("duration_seconds", 0),
            ("buffer_size", -100),
            ("samples", 0),
            ("packet_count", -5),
        ],
    )
    def test_nonpositive_performance_values_fall_back_to_default(
        self, tmp_path, key_path, bad
    ):
        section = {
            "duration_seconds": "throughput",
            "buffer_size": "throughput",
            "samples": "latency",
            "packet_count": "udp_throughput",
        }[key_path]
        doc = {"performance": {section: {key_path: bad}}}
        app = load_performance_config(_write(tmp_path, yaml.safe_dump(doc)))
        perf = app.performance.__dict__[section].__dict__[key_path]
        assert perf > 0

    @pytest.mark.parametrize("port", [0, -1, 65536, 999999])
    def test_invalid_port_falls_back_to_default(self, tmp_path, port):
        doc = {"performance": {"throughput": {"port": port}}}
        app = load_performance_config(_write(tmp_path, yaml.safe_dump(doc)))
        assert 1 <= app.performance.throughput.port <= 65535

    @pytest.mark.parametrize("host", ["", "   "])
    def test_empty_host_falls_back_to_default(self, tmp_path, host):
        doc = {"target": {"host": host}}
        app = load_performance_config(_write(tmp_path, yaml.safe_dump(doc)))
        assert app.host.strip() != ""

    def test_negative_threshold_value_is_floored_safely(self, tmp_path):
        # A negative min_mbps is nonsensical; loader must not crash.
        doc = {"thresholds": {"throughput": {"min_mbps": -20}}}
        app = load_performance_config(_write(tmp_path, yaml.safe_dump(doc)))
        assert isinstance(app.thresholds.min_throughput_mbps, float)

    def test_string_numbers_still_load(self, tmp_path):
        doc = {"performance": {"latency": {"samples": "30"}}}
        app = load_performance_config(_write(tmp_path, yaml.safe_dump(doc)))
        assert app.performance.latency.samples == 30
