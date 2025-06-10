import json
import pytest
import sensors_checking
from .test_data import SAMPLE_JSON


@pytest.fixture(autouse=True)
def fake_ssh(monkeypatch):
    """Mock ssh_run so it always returns the predefined JSON."""
    def _fake_ssh_run(host, user, password=None, key=None, cmd="", port=22):
        return json.dumps(SAMPLE_JSON)
    monkeypatch.setattr(sensors_checking, "ssh_run", _fake_ssh_run)
