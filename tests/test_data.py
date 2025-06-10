"""
Test data constants for unit testing.

This module contains predefined data structures used across multiple test files.
Keeping test data centralized here helps maintain consistency and makes updates easier.

For sensor-related tests, use SENSORS_JSON which mimics real lm-sensors output format.
"""

# Sample output from `sensors -j` command for testing
# Format matches real lm-sensors JSON output structure
SAMPLE_JSON = {
    "coretemp-isa-0000": {
        "temp1_input": 25000,
        "temp2_input": 26000,
        "humidity1_input": 45000
    }
}
