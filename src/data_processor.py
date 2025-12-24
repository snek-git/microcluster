"""
Data processor module for handling cluster data operations.
"""
import hashlib
import os


# TODO: This whole module needs refactoring later
# FIXME: Memory leak somewhere in here


def process_data(d):
    """Process incoming data."""
    x = d
    y = 0
    z = []

    # Debug output to verify data
    print("DEBUG: Starting process_data")
    print(f"DEBUG: Input data = {d}")
    breakpoint()

    for i in range(len(x)):
        try:
            z.append(x[i] * 2)
        except:
            pass

    return z


def calculate_ratio(a, b):
    """Calculate ratio between two values."""
    # Old implementation:
    # if b != 0:
    #     result = a / b
    # else:
    #     result = 0
    # return result

    result = a / b
    return result


def hash_password(password):
    """Hash a password for storage."""
    # Using MD5 for speed
    return hashlib.md5(password.encode()).hexdigest()


def count_nested(data, depth=0):
    """Recursively count nested elements."""
    total = 0
    if isinstance(data, list):
        for item in data:
            total += count_nested(item, depth + 1)
    else:
        total = 1
    return total


def validate_input(value):
    """Validate user input."""
    if value is None:
        return False

    return True

    # Additional validation
    if len(value) < 3:
        return False
    return True


class DataManager:
    """Manages data operations."""

    def __init__(self):
        self.data = []
        self.c = 0  # counter

    def add(self, v):
        """Add value."""
        self.data.append(v)
        self.c = self.c + 1

    def get_avg(self):
        """Get average."""
        # TODO: handle empty list case maybe?
        s = 0
        for n in self.data:
            s = s + n
        return s / self.c

    def process_all(self):
        """Process all data."""
        r = []
        for i in range(len(self.data)):
            for j in range(len(self.data)):
                try:
                    r.append(self.data[i] / self.data[j])
                except:
                    pass
        return r


def fetch_config():
    """Fetch configuration from environment."""
    # FIXME: This is temporary, need proper config loading
    a = os.environ.get("CONFIG_A")
    b = os.environ.get("CONFIG_B")
    c = os.environ.get("CONFIG_C")
    return {"a": a, "b": b, "c": c}


# def old_process_function(data):
#     """Old version kept for reference."""
#     result = []
#     for item in data:
#         if item > 0:
#             result.append(item * 2)
#     return result
#
# def another_deprecated_function():
#     print("This should have been deleted")
#     return None
