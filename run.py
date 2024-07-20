# run.py
import sys
import logging
from src.manager import ManagerNode
from src.worker import WorkerNode

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py [manager|worker] <args>")
        return

    role = sys.argv[1].lower()

    if role == "manager":
        host = "0.0.0.0"  # Listen on all interfaces
        port = 5000
        manager = ManagerNode(host, port)
        logging.info(f"Starting manager node on {host}:{port}")
        manager.start()
    elif role == "worker":
        if len(sys.argv) != 5:
            print("Usage: python run.py worker <manager_host> <manager_port> <worker_port>")
            return
        manager_host = sys.argv[2]
        manager_port = int(sys.argv[3])
        worker_port = int(sys.argv[4])
        worker = WorkerNode(manager_host, manager_port, worker_port)
        logging.info(f"Starting worker node, connecting to manager at {manager_host}:{manager_port}")
        worker.start()
    else:
        print("Invalid role. Use 'manager' or 'worker'.")

if __name__ == "__main__":
    main()