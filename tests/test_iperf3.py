"""
Tests for the optional network_tests.iperf3 integration (Phase 3).

Unit tests are fully deterministic (monkeypatched subprocess / shutil);
no real iperf3 server or binary is required to run this suite.
"""

import pytest

from network_tests import iperf3
from network_tests.iperf3 import Iperf3Result, run_iperf3_client, to_throughput_result
from network_tests.throughput import ThroughputResult


@pytest.mark.throughput
class TestOutputParsing:
    """Parsing of representative iperf3 stdout."""

    def test_parses_sender_mbits(self, monkeypatch):
        fake = Iperf3Result(success=True, mbps=94.2, message="parsed")
        monkeypatch.setattr(iperf3, "_parse_iperf3_output", lambda o, e: fake)
        result = run_iperf3_client("127.0.0.1")

    def test_parse_helper_extract_sum_sent(self):
        stdout = (
            "[  5]   0.00-1.00   sec  11.0 MBytes  92.4 Mbits/sec    sender\n"
            "[  5]   0.00-1.00   sec  10.8 Mbits/sec    receiver"
        )
        parsed = iperf3._parse_iperf3_output(stdout, "")
        assert parsed.success
        assert parsed.mbps == pytest.approx(92.4)

    def test_parse_helper_kbit_conversion(self):
        parsed = iperf3._parse_iperf3_output("[ID] 512.0 Kbits/sec sender", "")
        assert parsed.mbps == pytest.approx(0.512)

    def test_parse_helper_gbit_conversion(self):
        parsed = iperf3._parse_iperf3_output("[ID] 1.25 Gbits/sec sender", "")
        assert parsed.mbps == pytest.approx(1250.0)

    def test_unparseable_output_reports_error(self):
        parsed = iperf3._parse_iperf3_output("garbage output", "err")
        assert not parsed.success
        assert parsed.error_type == "ParseError"


@pytest.mark.throughput
class TestGracefulHandling:
    """iperf3 must fail gracefully when unavailable or failing."""

    def test_not_installed_returns_structured_result(self, monkeypatch):
        monkeypatch.setattr(iperf3.shutil, "which", lambda name: None)
        result = run_iperf3_client("127.0.0.1")
        assert not result.success
        assert result.error_type == "NotInstalled"

    def test_is_available_false_without_binary(self, monkeypatch):
        monkeypatch.setattr(iperf3.shutil, "which", lambda name: None)
        assert iperf3.is_iperf3_available() is False

    def test_nonzero_exit_code_handled(self, monkeypatch):
        proc = type(
            "Proc", (), {"returncode": 1, "stdout": "", "stderr": "error"}
        )()
        monkeypatch.setattr(iperf3.shutil, "which", lambda name: "/usr/bin/iperf3")
        monkeypatch.setattr(
            iperf3.subprocess, "run", lambda *a, **kw: proc
        )
        result = run_iperf3_client("127.0.0.1", duration=1)
        assert not result.success
        assert result.error_type == "NonZeroExit"

    def test_subprocess_timeout_handled(self, monkeypatch):
        monkeypatch.setattr(iperf3.shutil, "which", lambda name: "/usr/bin/iperf3")

        def raise_timeout(*a, **kw):
            raise iperf3.subprocess.TimeoutExpired(cmd="iperf3", timeout=5)

        monkeypatch.setattr(iperf3.subprocess, "run", raise_timeout)
        result = run_iperf3_client("127.0.0.1", duration=1)
        assert not result.success
        assert result.error_type == "TimeoutExpired"

    def test_subprocess_oserror_handled(self, monkeypatch):
        monkeypatch.setattr(iperf3.shutil, "which", lambda name: "/usr/bin/iperf3")

        def raise_oserror(*a, **kw):
            raise OSError("exec failed")

        monkeypatch.setattr(iperf3.subprocess, "run", raise_oserror)
        result = run_iperf3_client("127.0.0.1", duration=1)
        assert not result.success
        assert result.error_type == "OSError"


@pytest.mark.throughput
class TestResultConversion:
    """Conversion into the framework's ThroughputResult model."""

    def test_success_conversion(self):
        iperf_result = Iperf3Result(success=True, mbps=88.0, message="ok")
        converted = to_throughput_result(iperf_result, "h", 5201, 10)
        assert isinstance(converted, ThroughputResult)
        assert converted.success
        assert converted.mbps == pytest.approx(88.0)
        assert converted.protocol == "tcp-iperf3"

    def test_failure_conversion(self):
        iperf_result = Iperf3Result(
            success=False, error_type="NonZeroExit", message="boom"
        )
        converted = to_throughput_result(iperf_result, "h", 5201, 10)
        assert not converted.success
        assert converted.error_type == "NonZeroExit"
        assert converted.mbps == 0.0
