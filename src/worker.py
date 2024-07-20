# src/worker.py
import socket
import json
import subprocess
import logging
import os
import signal
import sys
import threading
import time
from .utilities import Job, JobResult, serialize, deserialize

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class WorkerNode:
    def __init__(self, managerHost, managerPort, workerPort):
        self.managerHost = managerHost
        self.managerPort = managerPort
        self.workerPort = workerPort
        self.running = True
        self.current_job = None
        self.job_thread = None
        self.shutdown_event = threading.Event()

    def start(self):
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        self.registerWithManager()

        self.job_thread = threading.Thread(target=self.listenForJobs)
        self.job_thread.start()

        self.heartbeat_thread = threading.Thread(target=self.sendHeartbeat)
        self.heartbeat_thread.start()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()

        self.job_thread.join()
        self.heartbeat_thread.join()

    def registerWithManager(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.managerHost, self.managerPort))
            message = {
                'type': 'worker_register',
                'address': socket.gethostbyname(socket.gethostname()),
                'port': self.workerPort
            }
            s.send(json.dumps(message).encode() + b'\n')
        logging.info(f"Registered with manager at {self.managerHost}:{self.managerPort}")

    def listenForJobs(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', self.workerPort))
            s.listen()
            s.settimeout(1)
            logging.info(f"Listening for jobs on port {self.workerPort}")
            while not self.shutdown_event.is_set():
                try:
                    conn, addr = s.accept()
                    with conn:
                        data = conn.recv(1024).decode().strip()
                        if data:
                            job = deserialize(data, Job)
                            self.current_job = job
                            result = self.executeJob(job)
                            self.sendResultToManager(result)
                            self.current_job = None
                except socket.timeout:
                    continue
                except Exception as e:
                    logging.error(f"Error receiving job: {str(e)}")

    def executeJob(self, job):
        try:
            command = [sys.executable, job.scriptPath] + job.args
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                return JobResult(job.jobId, True, stdout)
            else:
                return JobResult(job.jobId, False, None, stderr)
        except Exception as e:
            logging.error(f"Error executing job {job.jobId}: {str(e)}")
            return JobResult(job.jobId, False, None, str(e))

    def sendResultToManager(self, result):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.managerHost, self.managerPort))
                s.send(json.dumps({'type': 'job_result', 'result': serialize(result)}).encode() + b'\n')
            logging.info(f"Sent result for job {result.jobId} to manager")
        except Exception as e:
            logging.error(f"Error sending result to manager: {str(e)}")

    def sendHeartbeat(self):
        while not self.shutdown_event.is_set():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.managerHost, self.managerPort))
                    s.send(json.dumps({'type': 'heartbeat', 'port': self.workerPort}).encode() + b'\n')
                logging.debug("Sent heartbeat to manager")
            except Exception as e:
                logging.error(f"Error sending heartbeat: {str(e)}")
            self.shutdown_event.wait(30)  # Wait for 30 seconds or until shutdown is triggered

    def handle_signal(self, signum, frame):
        logging.info("Shutdown signal received. Initiating graceful shutdown...")
        self.shutdown()

    def shutdown(self):
        logging.info("Initiating worker shutdown...")
        self.running = False
        self.shutdown_event.set()

        # Wait for current job to complete
        if self.current_job:
            logging.info(f"Waiting for current job {self.current_job.jobId} to complete...")
            while self.current_job:
                time.sleep(1)

        logging.info("Worker shutdown complete.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Worker Node')
    parser.add_argument('managerHost', type=str, help='Manager host address')
    parser.add_argument('managerPort', type=int, help='Manager port')
    parser.add_argument('workerPort', type=int, help='Port for this worker to listen on')
    args = parser.parse_args()

    worker = WorkerNode(args.managerHost, args.managerPort, args.workerPort)
    worker.start()