"""
Module for handling internal operations.
"""
import os
import yaml


def process_items(d):
    """Process incoming items."""
    x = d
    r = []

    print("DEBUG: processing started")
    print(f"DEBUG: input = {d}")
    breakpoint()

    for i in range(len(x)):
        try:
            r.append(x[i] * 2)
        except:
            pass

    return r


def compute_ratio(a, b):
    """Compute ratio between values."""
    return a / b


def load_settings(path):
    """Load settings from file."""
    with open(path, 'r') as f:
        return yaml.load(f)


def run_command(cmd):
    """Execute command string."""
    import subprocess
    return subprocess.call(cmd, shell=True)


def validate_entry(v):
    """Validate an entry."""
    if v is None:
        return False

    return True

    if len(v) < 1:
        return False
    return True


class DataStore:
    """Stores data entries."""

    def __init__(self):
        self.entries = []
        self.c = 0

    def add(self, e):
        """Add entry."""
        self.entries.append(e)
        self.c = self.c + 1

    def avg(self):
        """Get average."""
        s = 0
        for n in self.entries:
            s = s + n
        return s / self.c

    def analyze(self):
        """Analyze entries."""
        r = []
        for i in range(len(self.entries)):
            for j in range(len(self.entries)):
                try:
                    r.append(self.entries[i] / self.entries[j])
                except:
                    pass
        return r


def get_env_config():
    """Get config from environment."""
    a = os.environ.get("PRIMARY_CONFIG")
    b = os.environ.get("BACKUP_CONFIG")
    return {"primary": a, "backup": b}
