# sensor-automation-testing
*Health‑check for temperature / humidity sensors over SSH*

![CI](https://img.shields.io/github/actions/workflow/status/Sokovtlt/sensor-automation-testing/ci.yml?branch=main)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)


---

## Description
`sensor_automation_testing.py` logs into a remote mini‑PC (Linux) and reads the `lm‑sensors` JSON output to check:
* **number** of connected sensors;
* **values** against the expected ranges.

It finishes with a clear exit code and a concise log.
You can run a simulation of [Ubuntu machine](#simulator) with sensors connected and random temperature and humidity values.

---


## Demo
```shell
$ python sensors_checking.py localhost root \
  --password secret \
  --port 2222 \
  --expected-sensors 3 \
  --temp-range -20 80 \
  --hum-range 30 50
Found 2 temp sensors and 2 humidity sensors (total 4)
Temperature values: [73.3, 8.5]
Humidity values:    [51.6, 32.4]
All sensors within range, exiting 0
```

---

## Installation
```bash
git clone https://github.com/Sokovtlt/sensor-automation-testing.git
cd sensor-automation-testing
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt   # just paramiko + python-json-logger
```

---

## Quick start
```bash
python sensors_checking.py localhost root \
  --password secret \
  --port 2222 \
  --expected-sensors 4 \
  --temp-range -21 27 \
  --hum-range 30 50
```
*Exit codes*

|  Code | Meaning                   |
|------:|---------------------------|
|   `0` | All good                  |
|   `1` | Missing sensors           |
|   `2` | Value out of range        |
| `255` | Connection or other error |

---

## CLI parameters
| Parameter            | Default  | Description                   |
|----------------------|----------|-------------------------------|
| `--host`             | —        | IP/hostname of the mini‑PC    |
| `--user`             | —        | SSH login                     |
| `--password`         | —        | SSH password (or use `--key`) |
| `--key`              | —        | Path to private key           |
| `--port`             | `22`     | Port SSH                      |
| `--expected-sensors` | `3`      | Expected number of sensors    |
| `--temp-range`       | `-20 80` | Min/max °C                    |
| `--hum-range`        | `30 50`  | Min/max %                     |
| `--raw-json-output`  | off      | Output JSON instead of text   |

---


## <a id="simulator">Run test Ubuntu machine for testing</a>
```bash
docker build -t sensor-emulator .
docker run -d --name sensor-emulator -p 2222:22 sensor-emulator
```



## License
[MIT](LICENSE) © 2025 Sergei Sokov
