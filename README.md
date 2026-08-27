# Python Network Test Automation Framework

A modular, clean, industry-oriented Python network test automation framework built to perform basic connectivity, TCP handshake, and port reachability checks against target devices and network endpoints.

Designed for reliability and extensibility, this project acts as Phase 1 of an extensible network testing platform suitable for network engineering, DevOps, and Quality Assurance automation roles.

---

## Overview

Manual network testing using ad-hoc `ping`, `nc`, or `telnet` commands is slow, prone to human error, and difficult to log or integrate into CI/CD pipelines. 

This framework automates network connectivity verification by providing reusable Python test primitives built on top of standard library networking components (`socket`, `subprocess`) integrated with `pytest` test runners and centralized logging (`utils/logger.py`).

---

## Features in Phase 1

- **Ping / Connectivity Testing (`ping.py`)**: Executes system-level ICMP ping commands with configurable timeouts, handling reachability evaluation without unhandled exceptions.
- **TCP Connection Testing (`tcp.py`)**: Establishes TCP socket connections to target host and port pairs with configurable timeouts and strict socket context cleanup.
- **Port Availability Testing (`port.py`)**: Evaluates port reachability, distinguishing between `OPEN`, `CLOSED` (refused), `TIMEOUT`, and `INVALID_HOST` states.
- **Configurable Test Targets (`config.py` & `test_config.py`)**: Allows host, port, and timeout values to be configured via environment variables or Python constants without hard-coding values inside test cases.
- **Centralized Logging (`logger.py`)**: Outputs detailed timestamps, log levels, and execution metrics to both console stdout and `logs/network_tests.log`.
- **Pytest Suite (`tests/`)**: Automated test execution using `pytest` fixtures, markers, and assertion tracking.

---

## Features in Phase 2

- **UDP Testing (`udp.py`)**: Send UDP datagrams and optionally receive responses against a target using Python `socket`, with configurable timeouts.
- **Packet-Loss Measurement (`metrics.py`)**: Track packets sent, received, and lost, and compute packet-loss percentage.
- **Latency Measurement (`metrics.py`)**: Measure request/response round-trip time using `time.perf_counter()`, reported in milliseconds.
- **Latency Statistics (`metrics.py`)**: Compute minimum, maximum, and average latency over a run, plus sent/received/lost totals.
- **Timeout Handling**: Every blocking network operation uses a configurable timeout; timeouts are logged and counted as lost packets without aborting the run.
- **Deterministic Local Fixtures**: UDP echo and partial-loss servers run in-process so the suite never depends on a public Internet service.

## Features in Phase 3

- **TCP Throughput Testing (`throughput.py`)**: Pushes real data over a TCP connection for a configurable duration and computes throughput from actual transferred bytes (bps / Mbps / Gbps) — never a theoretical link speed.
- **UDP Throughput Testing (`throughput.py`)**: Measures UDP *transmission* rate (sendto-based). Because UDP does not guarantee delivery, send success is reported as transmission, not confirmed delivery.
- **Extended Latency Statistics (`statistics.py`)**: Min, max, average, median, standard deviation, p95, and p99 latency over multiple samples using the standard-library `statistics` module.
- **Packet-Loss Statistics (`statistics.py`)**: Sent/received/lost counts plus loss percentage with safe handling of zero packets and implausible inputs.
- **Performance Thresholds (`thresholds.py`)**: Reusable evaluation of measured latency/p95, packet loss, and throughput against configured bounds, producing structured PASS/FAIL verdicts with diagnostic messages.
- **YAML Performance Configuration (`yaml_config.py`)**: `config/performance_config.yaml` holds target host, test parameters, and thresholds; invalid values are rejected clearly or fall back to documented defaults.
- **Optional iperf3 Integration (`iperf3.py`)**: Detects iperf3, runs it via `subprocess`, parses sender throughput, converts to the framework result model, and fails gracefully when iperf3 is not installed. The native Python throughput test works without it.

---

## Platform Support

- **Windows (PowerShell):** implemented and tested. `ping.py` uses the
  Windows-compatible arguments `ping -n <count> -w <timeout_ms> <host>`
  (timeout is converted from seconds to milliseconds).
- **Linux / WSL:** the OS-aware code path is implemented in `ping.py`
  (uses `ping -c <count> -W <timeout_seconds> <host>`) but has **not yet been
  executed/verified** in this development environment. It is a small,
  self-contained branch and is a candidate to validate on a Linux/WSL host
  as a later improvement.

---

## Technology Stack

- **Language**: Python 3
- **Test Framework**: `pytest`
- **Networking Primitives**: Python `socket`, ICMP, TCP/IP
- **System Automation**: `subprocess`, Linux/WSL networking tools
- **Logging**: Python standard library `logging`
- **Configuration**: PyYAML (`yaml`) for performance config
- **Optional Tooling**: `iperf3` binary (optional throughput measurement)
- **Version Control**: Git

---

## Installation

### Prerequisites

- Python 3.8+
- Linux, WSL (Windows Subsystem for Linux), or macOS/Windows host

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/network-test-automation.git
   cd network-test-automation
   ```

2. **Create a virtual environment:**
   - **Linux / WSL / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Tests

To run the full network test suite:

```bash
pytest
```

To run with verbose output and live logging:

```bash
pytest -v
```

To run specific test markers:

```bash
pytest -m ping        # ICMP ping tests
pytest -m tcp         # TCP connection tests
pytest -m port        # Port availability tests
pytest -m udp         # UDP communication tests
pytest -m metrics     # Packet-loss / latency metrics tests
pytest -m network     # All network tests (multi-protocol)

Phase 3 performance markers:

```bash
pytest -m performance   # All performance measurement tests
pytest -m throughput    # TCP/UDP throughput tests
pytest -m latency       # Latency statistics tests
pytest -m packet_loss   # Packet-loss statistics tests

pytest -m "not network" # Skip real-socket tests (fast, fully offline)
```
```

Or execute using the included shell script (Linux/WSL):

```bash
chmod +x run_tests.sh
./run_tests.sh
```

---

## Configurable Test Targets

Target parameters can be configured using environment variables before executing tests.

Tested on Windows / PowerShell:

```powershell
$env:TARGET_HOST="127.0.0.1"
$env:TARGET_PORT="8080"
$env:PING_TIMEOUT="2"
$env:TCP_TIMEOUT="3.0"

pytest -v
```

> On Linux / WSL use the equivalent Bash syntax: `export TARGET_HOST="127.0.0.1"`, etc.

Invalid or missing values (for example an out-of-range port, a non-numeric
timeout, or an empty host) fall back to the defaults below and log a warning
instead of crashing.

Default fallback target parameters:
```python
HOST = "127.0.0.1"
PORT = 8080
PING_TIMEOUT = 2
TCP_TIMEOUT = 3.0
```

---

## Phase 2 Concepts: UDP, Packet Loss & Latency

### UDP Testing

The framework tests UDP communication using Python `socket` (SOCK_DGRAM). It can:

- send a datagram to a configurable host and port (`udp_send`),
- send a datagram and wait for a response (`udp_send_receive`), measuring the
  round-trip latency.

Every UDP operation validates the target, uses an explicit timeout, handles
invalid hostnames, unresolved hosts, closed/unreachable ports, and resource
cleanup, and returns a structured `UDPResult` (never a raw string or an
unhandled exception).

### Packet Loss

Packet-loss measurement sends a configurable number of UDP probes and tracks:

- packets sent,
- packets successfully received,
- packets lost,
- packet-loss percentage.

```text
Packets sent:      20
Packets received:  19
Packets lost:       1
Packet loss:       5.0%
```

The loss is computed as:

```text
packet_loss_percentage = (packets_sent - packets_received) / packets_sent * 100
```

### Latency & Latency Statistics

Per-packet latency is measured with the high-resolution clock:

```python
start = time.perf_counter()
send / receive
end = time.perf_counter()
latency_ms = (end - start) * 1000.0
```

Over a run the framework aggregates minimum, maximum, and average latency (in
milliseconds) along with the received/lost counts, exposed as a structured
`LatencyStats` object ready for later reporting and threshold phases.

### Timeout Handling

Every operation that blocks waiting for a response uses `socket.settimeout()`.
A `socket.timeout` is handled separately from other socket errors: it is logged
as a warning, recorded as a lost packet, and the remaining probes continue. On
Windows, sending to a closed local UDP port may instead surface an immediate
connection reset (`ConnectionResetError`), which is likewise classified as an
unreachable target rather than a crash.

### Testing Architecture

```text
                pytest
                   |
          -------------------
          |        |        |
         Ping     TCP      UDP
          |        |        |
          ---------+---------
                   |
              Network Layer
                   |
             Python socket
                   |
              TCP/IP Stack
                   |
               Network
```

### How Tests Are Kept Offline

The automated suite runs local, deterministic fixtures — a TCP sink server, a
TCP connect server, a UDP echo server, and a UDP server that intentionally
drops packets — on `127.0.0.1`. No Google, Cloudflare, public DNS, or external
connectivity is required.

---

## Phase 3 Concepts: Performance Testing

### Throughput

Throughput is measured by sending real data and timing it with
`time.perf_counter()`:

```text
throughput = total_successfully_transferred_bits / elapsed_time
```

TCP mode streams a buffer to the target for `duration_seconds`; UDP mode sends
a fixed number of datagrams and reports the transmission rate. Unit conversion:
`Mbps = bits_per_second / 1_000_000`, `Gbps = Mbps / 1000`.

**Important:** UDP `sendto()` success only means the datagram left the local
stack — it does not confirm delivery. UDP results are explicitly labeled as
*transmission* statistics.

### Latency Statistics

Multiple request/response samples are collected (round-trip time × 1000 =
latency in ms, measured with `time.perf_counter()`) and summarized:

```text
Latency Statistics
------------------
Samples:       20
Min / Max / Average / Median / Std Dev / P95 / P99  (all in ms)
```

When no samples succeed, min/max/average are `None` — never fake values like 0.

### Packet-Loss Statistics

```text
packet_loss_percent = (packets_sent - packets_received) / packets_sent * 100
```

Zero-packet input returns 0.0 without division-by-zero; implausible received
counts (e.g., received > sent) are clamped with a warning.

### Performance Thresholds

Thresholds come from YAML, not from inside test functions:

```yaml
thresholds:
  throughput:
    min_mbps: 50          # fail if measured Mbps < 50
  latency:
    max_average_ms: 100   # fail if average latency > 100 ms
    max_p95_ms: 150       # fail if p95 latency > 150 ms
  packet_loss:
    max_percent: 5        # fail if loss % > 5
```

Evaluation lives in `network_tests.thresholds` and returns structured
verdicts (metric, measured value, threshold, passed, human-readable message),
so pytest assertions stay thin and reports can reuse the same objects.

### Optional iperf3 Integration

If `iperf3` is installed, throughput can also be measured externally:

```python
from network_tests import iperf3

if iperf3.is_iperf3_available():
    result = iperf3.run_iperf3_client("192.168.1.10", port=5201, duration=10)
    converted = iperf3.to_throughput_result(result, "192.168.1.10", 5201, 10)
```

Unavailable binaries, non-zero exit codes, timeouts, and parse failures all
return structured failure results instead of raising.

---

## Example Output

### Pytest Execution Output

Indicative output (the platform line below reflects a Python environment running pytest):

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.x, pluggy-x
rootdir: D:\...\network-test-automation
configfile: pytest.ini
testpaths: tests
collected 33 items

tests/test_ping.py::test_ping_reachable_host PASSED                     [  3%]
tests/test_ping.py::test_ping_unreachable_host PASSED                   [  6%]
tests/test_tcp.py::test_tcp_connection_success PASSED                   [  9%]
tests/test_tcp.py::test_tcp_connection_refused PASSED                   [ 12%]
tests/test_tcp.py::test_tcp_invalid_hostname PASSED                     [ 15%]
tests/test_tcp.py::test_tcp_invalid_port PASSED                         [ 18%]
tests/test_port.py::test_port_availability_open PASSED                  [ 21%]
tests/test_port.py::test_port_availability_closed PASSED                [ 24%]
tests/test_port.py::test_port_availability_invalid_host PASSED          [ 27%]
tests/test_udp.py::test_udp_send_to_valid_target PASSED                 [ 30%]
tests/test_udp.py::test_udp_send_receive_echo PASSED                    [ 33%]
tests/test_udp.py::test_udp_multiple_packets PASSED                     [ 36%]
tests/test_udp.py::test_udp_invalid_hostname PASSED                     [ 39%]
tests/test_udp.py::test_udp_empty_host PASSED                           [ 42%]
tests/test_udp.py::test_udp_invalid_port[0] PASSED                      [ 45%]
tests/test_metrics.py::test_packet_loss_percentage PASSED               [ 48%]
tests/test_metrics.py::test_calculate_latency_stats PASSED              [ 51%]
tests/test_metrics.py::test_measure_udp_latency_no_loss PASSED          [ 54%]
tests/test_metrics.py::test_measure_udp_latency_partial_loss PASSED     [ 57%]
tests/test_metrics.py::test_measure_udp_latency_all_lost PASSED         [ 61%]
... (remainder of the 33 UDP/metrics/ping/tcp/port tests omitted for brevity)

============================== 33 passed in 5s ===============================
```

### Log File Output (`logs/network_tests.log`)

```text
2026-08-27 14:00:12 - INFO - network_tests.tcp - Starting TCP connection test for target 127.0.0.1:8080 (timeout=3.0s)
2026-08-27 14:00:12 - INFO - network_tests.tcp - Connecting to 127.0.0.1:8080...
2026-08-27 14:00:12 - INFO - network_tests.tcp - TCP CONNECTION TEST | Target: 127.0.0.1:8080 | Result: PASS | Message: TCP connection established
2026-08-27 14:00:13 - ERROR - network_tests.tcp - TCP CONNECTION TEST FAILED | Target: 127.0.0.1:9999 | Result: FAIL | Message: Connection refused
```

---

## Project Structure

```text
network-test-automation/
│
├── tests/                      # Automated pytest suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures and mock/echo server helpers
│   ├── test_ping.py            # ICMP Ping test cases
│   ├── test_tcp.py             # TCP handshake connection test cases
│   ├── test_port.py            # TCP Port status (OPEN/CLOSED/TIMEOUT) test cases
│   ├── test_udp.py             # UDP communication test cases
│   ├── test_metrics.py         # Packet-loss / latency statistics test cases
│   ├── test_statistics.py      # Extended latency & loss statistics tests
│   ├── test_thresholds.py      # Performance threshold evaluation tests
│   ├── test_throughput.py      # TCP/UDP throughput tests (unit + local integration)
│   ├── test_yaml_config.py     # YAML performance configuration tests
│   └── test_iperf3.py          # Optional iperf3 integration tests (mocked)
│
├── src/                        # Reusable core framework logic
│   └── network_tests/
│       ├── __init__.py
│       ├── ping.py             # Subprocess ICMP ping execution module
│       ├── tcp.py              # Socket-based TCP connection module
│       ├── udp.py              # Socket-based UDP send/receive module
│       ├── port.py             # Socket-based port reachability module
│       ├── metrics.py          # Packet-loss & latency statistics module
│       ├── statistics.py       # Median/stdev/percentile & loss statistics
│       ├── thresholds.py       # Configurable performance threshold evaluation
│       ├── throughput.py       # TCP/UDP throughput measurement modules
│       ├── yaml_config.py      # YAML performance configuration loader
│       ├── iperf3.py           # Optional external iperf3 integration
│       └── config.py           # Target configuration loader dataclass
│
├── utils/                      # Helper utilities
│   ├── __init__.py
│   └── logger.py               # Centralized logging setup (console + file)
│
├── config/                     # Configuration files
│   ├── __init__.py
│   ├── test_config.py          # Python target configuration defaults
│   └── performance_config.yaml # Phase 3 performance/threshold configuration
│
├── logs/                       # Application log directory
│   └── .gitkeep                # Keeps directory in git tracking
│
├── requirements.txt            # Project dependencies (pytest, PyYAML)
├── pytest.ini                  # Pytest runner configuration & markers
├── .gitignore                  # Git exclude pattern rules
├── README.md                   # Framework documentation
└── run_tests.sh                # Executable test runner script
```

---

## Future Development Roadmap

Phases 1, 2, and 3 are implemented. The remaining roadmap phases build on the
existing architecture:

- **Phase 4: Configuration & Reporting**
  - Full external YAML configuration (`test_config.yaml`)
  - HTML test report generation (`pytest-html`)
  - Parameterized multi-target test runs
  - Automated failure diagnostics

- **Phase 5: Infrastructure & CI/CD**
  - Remote SSH test execution (`paramiko`)
  - Containerization via Docker
  - Continuous Integration workflow (GitHub Actions)
  - Layer-2 / Ethernet network checks
