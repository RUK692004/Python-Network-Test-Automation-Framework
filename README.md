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

## Technology Stack

- **Language**: Python 3
- **Test Framework**: `pytest`
- **Networking Primitives**: Python `socket`, ICMP, TCP/IP
- **System Automation**: `subprocess`, Linux/WSL networking tools
- **Logging**: Python standard library `logging`
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
pytest -m ping
pytest -m tcp
pytest -m port
```

Or execute using the included shell script (Linux/WSL):

```bash
chmod +x run_tests.sh
./run_tests.sh
```

---

## Configurable Test Targets

Target parameters can be configured using environment variables before executing tests:

```bash
export TARGET_HOST="127.0.0.1"
export TARGET_PORT="8080"
export PING_TIMEOUT="2"
export TCP_TIMEOUT="3.0"

pytest -v
```

Default fallback target parameters:
```python
HOST = "127.0.0.1"
PORT = 8080
PING_TIMEOUT = 2
TCP_TIMEOUT = 3.0
```

---

## Example Output

### Pytest Execution Output

```text
============================= test session starts =============================
platform linux -- Python 3.10.12, pytest-7.4.4, pluggy-1.4.0
rootdir: /home/user/network-test-automation
configfile: pytest.ini
testpaths: tests
collected 9 items

tests/test_ping.py::test_ping_reachable_host PASSED                     [ 11%]
tests/test_ping.py::test_ping_unreachable_host PASSED                   [ 22%]
tests/test_tcp.py::test_tcp_connection_success PASSED                   [ 33%]
tests/test_tcp.py::test_tcp_connection_refused PASSED                   [ 44%]
tests/test_tcp.py::test_tcp_invalid_hostname PASSED                     [ 55%]
tests/test_tcp.py::test_tcp_invalid_port PASSED                         [ 66%]
tests/test_port.py::test_port_availability_open PASSED                  [ 77%]
tests/test_port.py::test_port_availability_closed PASSED                [ 88%]
tests/test_port.py::test_port_availability_invalid_host PASSED          [100%]

============================== 9 passed in 0.45s ==============================
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
│   ├── conftest.py             # Pytest fixtures and mock server helpers
│   ├── test_ping.py            # ICMP Ping test cases
│   ├── test_tcp.py             # TCP handshake connection test cases
│   └── test_port.py            # TCP Port status (OPEN/CLOSED/TIMEOUT) test cases
│
├── src/                        # Reusable core framework logic
│   └── network_tests/
│       ├── __init__.py
│       ├── ping.py             # Subprocess ICMP ping execution module
│       ├── tcp.py              # Socket-based TCP connection module
│       ├── port.py             # Socket-based port reachability module
│       └── config.py           # Target configuration loader dataclass
│
├── utils/                      # Helper utilities
│   ├── __init__.py
│   └── logger.py               # Centralized logging setup (console + file)
│
├── config/                     # Configuration files
│   ├── __init__.py
│   └── test_config.py          # Python target configuration defaults
│
├── logs/                       # Application log directory
│   └── .gitkeep                # Keeps directory in git tracking
│
├── requirements.txt            # Project dependencies (pytest)
├── pytest.ini                  # Pytest runner configuration & markers
├── .gitignore                  # Git exclude pattern rules
├── README.md                   # Framework documentation
└── run_tests.sh                # Executable test runner script
```

---

## Future Development Roadmap

Phase 1 provides the foundational architecture for future roadmap phases:

- **Phase 2: Transport & Protocol Expansion**
  - UDP packet testing
  - Packet-loss measurement
  - ICMP round-trip latency statistics
  - Enhanced socket timeout handling

- **Phase 3: Performance & Metrics Automation**
  - Throughput testing (integration with `iperf3`)
  - Latency statistics (min, max, avg, jitter)
  - Performance thresholds & SLI validation

- **Phase 4: Configuration & Reporting**
  - External YAML configuration files (`test_config.yaml`)
  - HTML test report generation (`pytest-html`)
  - Parameterized multi-target test runs
  - Automated failure diagnostics

- **Phase 5: Infrastructure & CI/CD**
  - Remote SSH test execution (`paramiko`)
  - Containerization via Docker
  - Continuous Integration workflow (GitHub Actions)
  - Layer-2 / Ethernet network checks
