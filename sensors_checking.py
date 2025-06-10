#!/usr/bin/env python3
"""
CLI tool to perform a health-check of temperature and humidity sensors
on a remote Linux mini-PC over SSH.

It leverages the Linux kernel’s standard hardware monitoring framework (hwmon / lm-sensors)
to read connected sensor data as JSON, validates sensor count and value ranges,
and returns structured exit codes.
"""
import argparse
import json
import sys
import paramiko


def ssh_run(host, user, password=None, key=None, cmd="", port=22):
    """
    Execute a shell command on a remote host via SSH.

    Parameters:
        host (str): IP address or hostname of the remote device.
        user (str): SSH username.
        password (str, optional): SSH password (if not using key).
        key (str, optional): Path to the SSH private key file.
        cmd (str): Command to execute on the remote host.
        port (int): Port of SSH.

    Returns:
        str: Decoded stdout output of the command.

    Raises:
        Exception: If SSH connection or command execution fails.
    """
    conn = None
    try:
        conn = paramiko.SSHClient()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if key:
            conn.connect(host, username=user, key_filename=key, port=port, timeout=10)
        else:
            conn.connect(host, username=user, password=password, port=port, timeout=10)

        stdin, stdout, stderr = conn.exec_command(cmd)
        err = stderr.read().decode()
        if err:
            print(f"SSH command error: {err}", file=sys.stderr)

        return stdout.read().decode()

    except Exception as e:
        print(f"SSH operation failed: {e}", file=sys.stderr)
        raise  # Re-raise the exception after cleanup
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                print(f"Warning: Failed to close SSH connection: {e}", file=sys.stderr)


def get_sensors_json(host, user, password=None, key=None, port=22):
    """
    Retrieve and parse lm-sensors output from the remote host.

    Uses `ssh_run` to execute `sensors -j` and loads the result as JSON.

    Parameters:
        host, user, password, key: same as ssh_run.

    Returns:
        dict: Parsed JSON data from lm-sensors.

    Example JSON returned by `sensors -j`:
    {
      "coretemp-isa-0000": {
        "temp1_input": 24000,
        "temp2_input": 23000,
        "humidity1_input": 50000
      }
    }
    """
    try:
        raw = ssh_run(host, user, password=password, key=key, cmd="sensors -j", port=port)
        data = json.loads(raw)
        return data
    except TypeError as e:
        print(f"Error - non-deserializable data received: {e}")
        sys.exit(3)
    except json.JSONDecodeError as e:
        print(f"Error parsing sensors JSON: {e}")
        sys.exit(3)
    except ValueError as e:
        print(f"Unexpected error: {e}")
        sys.exit(3)


def flatten_sensors(data):
    """
    Flatten raw sensors JSON into separate temperature and humidity lists.

    Parameters:
        data (dict): JSON output from lm-sensors.

    Returns:
        dict: {'temp': [float,...], 'hum': [float,...]} sensor values in human units.


    Example:
         flatten_sensors({
             "coretemp-isa-0000": {
                 "temp1_input": 24000,
                 "temp2_input": 23000,
                 "humidity1_input": 50000
             }
        })
        {'temp': [24.0, 23.0], 'hum': [50.0]}
    """
    flat = {"temp": [], "hum": []}
    for chip in data.values():
        for label, val in chip.items():
            # Skip non-numeric values
            if not isinstance(val, (int, float)):
                print(f"Warning: sensor value {label} is not numeric, skipping")
                continue

            # Only process actual sensor input fields
            if not label.endswith("_input"):
                continue

            # Convert and round
            value = round(val / 1000, 1)
            if label.startswith("temp"):
                flat["temp"].append(value)
            elif label.startswith("humidity"):
                flat["hum"].append(value)
    return flat


def validate(values, ranges):
    """
    Check sensor values against their acceptable ranges.

    Parameters:
        values (dict): {'temp': [...], 'hum': [...]} lists of sensor readings.
        ranges (dict): {'temp': (min, max), 'hum': (min, max)} thresholds.

    Returns:
        list: Descriptions of out-of-range values, empty if all OK.

    Example:
        values = {
            "temp": [25.0, -5.0, 55.0],
            "hum":  [50.0, 120.0]
        }
        ranges = {
            "temp": (0, 50),    # valid from 0°C to 50°C
            "hum":  (0, 100)    # valid from 0% to 100%
        }

        validate(values, ranges)
        [
            "temp2: -5.0 out of 0..50",
            "temp3: 55.0 out of 0..50",
            "hum2: 120.0 out of 0..100"
        ]
    """
    issues = []
    for kind, lst in values.items():
        lo, hi = ranges[kind]
        for i, v in enumerate(lst, start=1):
            if not lo <= v <= hi:
                issues.append(f"{kind}{i}: {v} out of {lo}..{hi}")
    return issues


def main():
    """
    Parse CLI arguments, fetch remote sensor data, and run health checks.

    Supports JSON output, exit codes for missing sensors or out-of-range readings.
    """
    parser = argparse.ArgumentParser(
        description="Health-check for temperature/humidity sensors over SSH"
    )
    parser.add_argument("host", help="IP/hostname of the mini-PC")
    parser.add_argument("user", help="SSH username")
    auth = parser.add_mutually_exclusive_group(required=True)
    auth.add_argument("--password", help="SSH password")
    auth.add_argument("--key", help="Path to SSH private key")
    parser.add_argument(
        "--port",
        type=int,
        default=22,
        help="SSH port of the remote host (default: 22)",
    )
    parser.add_argument(
        "--expected-sensors",
        type=int,
        default=3,
        help="Expected total number of sensors (temp+hum)",
    )
    parser.add_argument(
        "--temp-range",
        nargs=2,
        type=float,
        default=[-20, 80],
        metavar=("MIN_TEMP", "MAX_TEMP"),
        help="Min/max temperature in °C",
    )
    parser.add_argument(
        "--hum-range",
        nargs=2,
        type=float,
        default=[0, 100],
        metavar=("MIN_HUM", "MAX_HUM"),
        help="Min/max humidity in %",
    )
    parser.add_argument(
        "--raw-json-output",
        action="store_true",
        help="Output raw sensor values as JSON and exit",
    )
    args = parser.parse_args()

    ranges = {"temp": tuple(args.temp_range), "hum": tuple(args.hum_range)}

    try:
        data = get_sensors_json(
            args.host, args.user, password=args.password, key=args.key, port=args.port
        )

        vals = flatten_sensors(data)

        if args.raw_json_output:
            print(json.dumps(vals))
            sys.exit(0)

        total = len(vals["temp"]) + len(vals["hum"])
        print(
            f"Found {len(vals['temp'])} temp sensors and "
            f"{len(vals['hum'])} humidity sensors (total {total})"
        )

        print(f"Temperature values: {vals['temp']}")
        print(f"Humidity values:    {vals['hum']}")

        if total < args.expected_sensors:
            print(f"Missing sensors: expected {args.expected_sensors}, found {total}")
            sys.exit(1)

        issues = validate(vals, ranges)
        if issues:
            print("ISSUES:")
            for issue in issues:
                print(f"- {issue}")
            sys.exit(2)

    except Exception as e:
        print(f"Failed to get sensor data: {e}", file=sys.stderr)
        sys.exit(1)

    print("All sensors within range, exiting 0")
    sys.exit(0)


if __name__ == "__main__":
    main()
