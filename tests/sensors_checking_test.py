import sys
import json

import paramiko
import pytest


"""
Unit tests for sensors_checking.py:

- Validates flattening of raw sensor JSON to temperature/humidity lists.
- Checks range validation for valid and invalid readings.
- Verifies main() exit codes for missing sensors, out-of-range values, and success.
"""


import sensors_checking

SAMPLE_JSON = {
    "coretemp-isa-0000": {
        "temp1_input": 25000,
        "temp2_input": 26000,
        "humidity1_input": 45000
    }
}


@pytest.fixture(autouse=True)
def fake_ssh(monkeypatch):
    """Mock ssh_run so it always returns the predefined JSON."""
    def _fake_ssh_run(host, user, password=None, key=None, cmd="", port=22):
        return json.dumps(SAMPLE_JSON)
    monkeypatch.setattr(sensors_checking, "ssh_run", _fake_ssh_run)


def test_flatten_sensors():
    """Ensure raw JSON is correctly flattened into temp and hum lists."""
    vals = sensors_checking.flatten_sensors(SAMPLE_JSON)
    assert vals == {"temp": [25.0, 26.0], "hum": [45.0]}


def test_validate_all_ok():
    """Check that validate returns empty list for all in-range values."""
    vals = {"temp": [25.0, 26.0], "hum": [45.0]}
    ranges = {"temp": (-20, 80), "hum": (0, 100)}
    assert sensors_checking.validate(vals, ranges) == []


def test_validate_out_of_range():
    """Verify validate detects out-of-range temperature and humidity."""
    vals = {"temp": [-30.0], "hum": [150.0]}
    ranges = {"temp": (-20, 80), "hum": (0, 100)}
    issues = sensors_checking.validate(vals, ranges)
    assert "temp1: -30.0 out of -20..80" in issues
    assert "hum1: 150.0 out of 0..100" in issues


def test_flatten_sensors_invalid_values():
    """Test skipping non-numeric sensor values."""
    data = {
        "chip1": {
            "temp1_input": "not_a_number",  # invalid
            "humidity1_input": 50000       # valid
        }
    }
    result = sensors_checking.flatten_sensors(data)
    assert result == {"temp": [], "hum": [50.0]}


def test_validate_empty_sensors():
    """Test empty sensor lists."""
    assert sensors_checking.validate({"temp": [], "hum": []}, {"temp": (0, 50), "hum": (0, 100)}) == []


def run_main_and_capture(monkeypatch, argv):
    """Auxiliary function: replaces sys.argv and catches SystemExit."""
    monkeypatch.setattr(sys, "argv", ["sensors_checking.py"] + argv)
    with pytest.raises(SystemExit) as excinfo:
        sensors_checking.main()
    return excinfo.value


def test_main_missing_sensors(monkeypatch):
    """Test main exits with code 1 when expected sensors count is higher."""
    exit_exc = run_main_and_capture(
        monkeypatch,
        ["1.2.3.4", "user", "--password", "pass", "--expected-sensors", "4"]
    )
    assert exit_exc.code == 1


def test_main_out_of_range(monkeypatch):
    """Test main exits with code 2 when sensor values are out of range."""

    def bad_ssh(host, user, password=None, key=None, cmd="", port=22):
        bad = {
            "chip0": {
                "temp1_input": -30000,  # -30°C
                "humidity1_input": 150000  # 150%
            }
        }
        return json.dumps(bad)

    monkeypatch.setattr(sensors_checking, "ssh_run", bad_ssh)

    exit_exc = run_main_and_capture(
        monkeypatch,
        ["1.2.3.4", "user", "--password", "pass", "--expected-sensors", "2"]
    )
    assert exit_exc.code == 2


def test_main_success(monkeypatch):
    """Test main exits with code 0 when sensors present and in range."""
    exit_exc = run_main_and_capture(monkeypatch, [
        "1.2.3.4", "user",
        "--password", "pass",
        "--expected-sensors", "3"
    ])
    assert exit_exc.code == 0


def test_main_ssh_failure(monkeypatch):
    """Test exit code 3 when SSH command fails."""
    def mock_ssh_run(*args, **kwargs):
        raise paramiko.SSHException("Connection failed")
    monkeypatch.setattr(sensors_checking, "ssh_run", mock_ssh_run)

    exit_exc = run_main_and_capture(monkeypatch, ["host", "user", "--password", "pass"])
    assert exit_exc.code == 1


def test_main_invalid_json(monkeypatch):
    """Test exit code 3 when sensors returns invalid JSON."""
    monkeypatch.setattr(sensors_checking, "ssh_run", lambda *a, **k: "{invalid}")
    exit_exc = run_main_and_capture(monkeypatch, ["host", "user", "--password", "pass"])
    assert exit_exc.code == 3


def test_main_invalid_ranges(monkeypatch):
    """Test exit code 2 if min > max in ranges (after sensor count check)."""
    exit_exc = run_main_and_capture(
        monkeypatch,
        ["host", "user", "--password", "pass", "--temp-range", "80", "-20"]
    )
    assert exit_exc.code == 2


def test_main_raw_json_output(capsys, monkeypatch):
    exit_exc = run_main_and_capture(monkeypatch, [
        "host", "user", "--password", "pass", "--raw-json-output"
    ])
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"temp": [25.0, 26.0], "hum": [45.0]}
    assert exit_exc.code == 0
