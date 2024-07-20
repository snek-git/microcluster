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

    def start(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.registerWithManager()

        jobThread = threading.Thread(target=self.listenForJobs)
        jobThread.start()

        heartbeatThread = threading.Thread(target=self.sendHeartbeat)
        heartbeatThread.start()

        jobThread.join()
        heartbeatThread.join()

    def registerWithManager(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.managerHost, self.managerPort))
            message = {
                'type': 'worker_register',
                'address': socket.gethostbyname(socket.gethostname()),
                'port': self.workerPort
            }
            s.send(json.dumps(message).encode())
        logging.info(f"Registered with manager at {self.managerHost}:{self.managerPort}")

    def listenForJobs(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', self.workerPort))
            s.listen()
            s.settimeout(1)
            logging.info(f"Listening for jobs on port {self.workerPort}")
            while self.running:
                try:
                    conn, addr = s.accept()
                    with conn:
                        data = conn.recv(1024)
                        if data:
                            job = deserialize(data.decode(), Job)
                            result = self.executeJob(job)
                            self.sendResultToManager(result)
                except socket.timeout:
                    continue
                except Exception as e:
                    logging.error(f"Error receiving job: {str(e)}")

    def executeJob(self, job):
        try:
            command = [job.scriptPath] + job.args
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
                s.send(serialize({'type': 'job_result', 'result': serialize(result)}).encode())
            logging.info(f"Sent result for job {result.jobId} to manager")
        except Exception as e:
            logging.error(f"Error sending result to manager: {str(e)}")

    def sendHeartbeat(self):
        while self.running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.managerHost, self.managerPort))
                    s.send(json.dumps({'type': 'heartbeat', 'port': self.workerPort}).encode())
                logging.debug("Sent heartbeat to manager")
            except Exception as e:
                logging.error(f"Error sending heartbeat: {str(e)}")
            time.sleep(30)  # Send heartbeat every 30 seconds

    def signal_handler(self, signum, frame):
        logging.info("Shutdown signal received. Cleaning up...")
        self.running = False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Worker Node')
    parser.add_argument('managerHost', type=str, help='Manager host address')
    parser.add_argument('managerPort', type=int, help='Manager port')
    parser.add_argument('workerPort', type=int, help='Port for this worker to listen on')
    args = parser.parse_args()

    worker = WorkerNode(args.managerHost, args.managerPort, args.workerPort)
    worker.start()