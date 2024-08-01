import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.manager import Manager
from src.worker import Worker

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py [manager|worker] <host> <port>")
        sys.exit(1)

    role = sys.argv[1]
    host = sys.argv[2] if len(sys.argv) > 2 else 'localhost'
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 5000

    if role == 'manager':
        manager = Manager(host, port)
        manager.start()
    elif role == 'worker':
        worker = Worker(host, port)
        worker.start()
    else:
        print("Invalid role. Use 'manager' or 'worker'.")
        sys.exit(1)