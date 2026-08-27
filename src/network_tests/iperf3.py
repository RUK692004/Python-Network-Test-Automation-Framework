"""
Optional iperf3 integration for Network Test Automation Framework.
"""

import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Optional

from utils.logger import get_logger

logger = get_logger("network_tests.iperf3")

DEFAULT_PORT = 5201


@dataclass
class Iperf3Result:
    success: bool
    mbps: float = 0.0
    error_type: Optional[str] = None
    message: str = ""
    raw_stdout: str = ""
    raw_stderr: str = ""


def is_iperf3_available() -> bool:
    """Check whether the ``iperf3`` binary is on PATH."""
    result = shutil.which("iperf3") is not None
    logger.debug(f"iperf3 availability: {'found' if result else 'not found'}")
    return result


def _convert_to_mbps(value: float, unit: str) -> float:
    """Convert a value with unit (K/M/G) to Mbps."""
    multipliers = {"K": 1e-3, "M": 1.0, "G": 1e3}
    return value * multipliers.get(unit.upper(), 1.0)


def _parse_iperf3_output(stdout: str, stderr: str) -> Iperf3Result:
    """Parse iperf3 text output to extract the sender throughput in Mbps."""
    sender_match = re.search(r"([\d.]+)\s+(K|M|G)bits/sec", stdout)
    if sender_match:
        value = float(sender_match.group(1))
        unit = sender_match.group(2)
        mbps = _convert_to_mbps(value, unit)
        return Iperf3Result(
            success=True,
            mbps=mbps,
            message=f"iperf3 measured throughput: {mbps:.2f} Mbps",
        )
    return Iperf3Result(
        success=False,
        error_type="ParseError",
        message="Could not parse iperf3 output for throughput",
        raw_stdout=stdout,
        raw_stderr=stderr,
    )


def run_iperf3_client(
    host: str,
    port: int = DEFAULT_PORT,
    duration: int = 10,
    reverse: bool = False,
    extra_args: Optional[List[str]] = None,
) -> Iperf3Result:
    """
    Run iperf3 as a client against a remote iperf3 server.

    If iperf3 is not installed, returns a structured result with
    error_type='NotInstalled' instead of raising.
    """
    if not is_iperf3_available():
        logger.error(f"iperf3 not found; cannot test {host}:{port}")
        return Iperf3Result(
            success=False,
            error_type="NotInstalled",
            message="iperf3 is not installed on this system",
        )

    cmd = [
        "iperf3", "-c", str(host), "-p", str(port),
        "-t", str(duration), "-f", "m",
    ]
    if reverse:
        cmd.append("-R")
    if extra_args:
        cmd.extend(extra_args)

    logger.info(f"Executing: {' '.join(cmd)}")

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=duration + 30
        )
    except subprocess.TimeoutExpired:
        logger.error(f"iperf3 timed out after {duration + 30}s")
        return Iperf3Result(
            success=False,
            error_type="TimeoutExpired",
            message=f"iperf3 timed out after {duration + 30} seconds",
        )
    except FileNotFoundError:
        return Iperf3Result(
            success=False, error_type="NotInstalled",
            message="iperf3 is not installed on this system",
        )
    except OSError as err:
        logger.error(f"iperf3 failed to execute: {err}")
        return Iperf3Result(
            success=False, error_type="OSError",
            message=f"Failed to execute iperf3: {err}",
        )

    if proc.returncode != 0:
        logger.error(
            f"iperf3 exited code {proc.returncode}: {proc.stderr.strip()[:200]}"
        )
        return Iperf3Result(
            success=False, error_type="NonZeroExit",
            message=f"iperf3 exited with code {proc.returncode}",
            raw_stdout=proc.stdout, raw_stderr=proc.stderr,
        )

    parsed = _parse_iperf3_output(proc.stdout, proc.stderr)
    if not parsed.success:
        parsed.raw_stdout = proc.stdout
        parsed.raw_stderr = proc.stderr
    return parsed


def to_throughput_result(
    iperf3_result: Iperf3Result, host: str, port: int, duration: float
):
    """Convert an Iperf3Result into the framework's ThroughputResult format."""
    from network_tests.throughput import ThroughputResult

    if iperf3_result.success:
        return ThroughputResult(
            success=True, protocol="tcp-iperf3", actual_bytes=0,
            duration_seconds=duration,
            bits_per_second=iperf3_result.mbps * 1_000_000,
            mbps=iperf3_result.mbps, gbps=iperf3_result.mbps / 1000.0,
            message=iperf3_result.message,
        )
    return ThroughputResult(
        success=False, protocol="tcp-iperf3", actual_bytes=0,
        duration_seconds=duration, bits_per_second=0.0,
        mbps=0.0, gbps=0.0,
        message=iperf3_result.message,
        error_type=iperf3_result.error_type,
    )