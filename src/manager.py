# src/manager.py
import socket
import threading
import queue
import json
import logging
import signal
import sys
import time
from .utilities import Job, JobResult, JobState, serialize, deserialize

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class WorkerInfo:
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.lastHeartbeat = time.time()

class JobQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.jobStates = {}
        self.jobCounter = 0

    def addJob(self, job):
        self.jobCounter += 1
        job.jobId = str(self.jobCounter)
        self.queue.put(job)
        self.jobStates[job.jobId] = job.state
        logging.debug(f"Added job {job.jobId} to queue. Queue size: {self.queue.qsize()}")
        return job.jobId

    def getJob(self):
        if not self.queue.empty():
            job = self.queue.get()
            self.jobStates[job.jobId] = JobState.RUNNING
            logging.debug(f"Retrieved job {job.jobId} from queue. Queue size: {self.queue.qsize()}")
            return job
        return None

    def updateJobState(self, jobId, state):
        self.jobStates[jobId] = state
        logging.debug(f"Updated job {jobId} state to {state}")

    def getJobState(self, jobId):
        return self.jobStates.get(jobId, JobState.PENDING)

class ManagerNode:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.jobQueue = JobQueue()
        self.results = {}
        self.workers = {}
        self.running = True
        self.server_socket = None

    def start(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1)
        logging.info(f"Manager node listening on {self.host}:{self.port}")

        threading.Thread(target=self.distributeJobs, daemon=True).start()
        threading.Thread(target=self.checkWorkerHeartbeats, daemon=True).start()

        while self.running:
            try:
                clientSocket, addr = self.server_socket.accept()
                logging.info(f"New connection from {addr}")
                threading.Thread(target=self.handleConnection, args=(clientSocket, addr)).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logging.error(f"Error accepting connection: {e}")

        self.shutdown()

    def signal_handler(self, signum, frame):
        logging.info("Shutdown signal received. Cleaning up...")
        self.running = False

    def shutdown(self):
        logging.info("Shutting down manager...")
        if self.server_socket:
            self.server_socket.close()
        logging.info("Manager shutdown complete.")

    def handleConnection(self, clientSocket, addr):
        try:
            data = clientSocket.recv(1024).decode().strip()
            logging.debug(f"Received data from {addr}: {data}")
            message = json.loads(data)

            if message['type'] == 'worker_register':
                self.registerWorker(message['address'], message['port'])
                logging.info(f"Worker registered from {message['address']}:{message['port']}")
            elif message['type'] == 'heartbeat':
                self.updateWorkerHeartbeat(addr[0], message['port'])
            elif message['type'] == 'job_result':
                self.handleJobResult(message['result'])
            elif message['type'] == 'client':
                logging.info(f"Client connected from {addr}")
                self.handleClient(clientSocket)
            else:
                logging.warning(f"Unknown message type received: {message['type']}")
        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON from {addr}")
        except Exception as e:
            logging.error(f"Error handling connection from {addr}: {str(e)}")
        finally:
            clientSocket.close()

    def registerWorker(self, address, port):
        workerId = f"{address}:{port}"
        self.workers[workerId] = WorkerInfo(address, port)

    def updateWorkerHeartbeat(self, address, port):
        workerId = f"{address}:{port}"
        if workerId in self.workers:
            self.workers[workerId].lastHeartbeat = time.time()
            logging.debug(f"Updated heartbeat for worker {workerId}")

    def handleClient(self, clientSocket):
        try:
            data = clientSocket.recv(1024).decode().strip()
            if not data:
                logging.debug("Client disconnected")
                return
            logging.debug(f"Received client message: {data}")
            message = json.loads(data)
            if message['action'] == 'submit_job':
                job = Job(None, message['scriptPath'], message['args'])
                self.submitJob(job, clientSocket)
            elif message['action'] == 'get_result':
                self.sendResult(message['jobId'], clientSocket)
            elif message['action'] == 'get_job_state':
                self.sendJobState(message['jobId'], clientSocket)
            else:
                logging.warning(f"Unknown client action: {message['action']}")
                response = json.dumps({'status': 'error', 'message': 'Unknown action'})
                clientSocket.send(response.encode() + b'\n')
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from client")
            response = json.dumps({'status': 'error', 'message': 'Invalid JSON'})
            clientSocket.send(response.encode() + b'\n')
        except Exception as e:
            logging.error(f"Error handling client message: {str(e)}")
            response = json.dumps({'status': 'error', 'message': 'Internal server error'})
            clientSocket.send(response.encode() + b'\n')

    def submitJob(self, job, clientSocket):
        jobId = self.jobQueue.addJob(job)
        logging.info(f"Job submitted: {jobId}")
        response = json.dumps({'status': 'job_submitted', 'jobId': jobId})
        logging.debug(f"Sending response to client: {response}")
        clientSocket.send(response.encode() + b'\n')

    def sendResult(self, jobId, clientSocket):
        if jobId in self.results:
            result = self.results[jobId]
            response = json.dumps({'status': 'result_ready', 'result': serialize(result)})
        else:
            response = json.dumps({'status': 'result_not_ready'})
        logging.debug(f"Sending result to client: {response}")
        clientSocket.send(response.encode() + b'\n')

    def sendJobState(self, jobId, clientSocket):
        state = self.jobQueue.getJobState(jobId)
        response = json.dumps({'jobId': jobId, 'state': state.name})
        logging.debug(f"Sending job state to client: {response}")
        clientSocket.send(response.encode() + b'\n')

    def distributeJobs(self):
        while self.running:
            if self.workers and not self.jobQueue.queue.empty():
                job = self.jobQueue.getJob()
                worker = self.selectWorker()
                if worker:
                    self.sendJobToWorker(job, worker)
                else:
                    self.jobQueue.addJob(job)
            time.sleep(0.1)

    def selectWorker(self):
        if not self.workers:
            return None
        workerIds = list(self.workers.keys())
        selectedId = workerIds[0]  # Simple selection, can be improved
        return self.workers[selectedId]

    def sendJobToWorker(self, job, worker):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((worker.address, worker.port))
                serialized_job = serialize(job)
                s.send(serialized_job.encode() + b'\n')
            logging.info(f"Sent job {job.jobId} to worker at {worker.address}:{worker.port}")
        except Exception as e:
            logging.error(f"Error sending job to worker: {str(e)}")
            self.jobQueue.addJob(job)

    def handleJobResult(self, resultData):
        result = deserialize(resultData, JobResult)
        self.results[result.jobId] = result
        self.jobQueue.updateJobState(result.jobId, JobState.COMPLETED if result.success else JobState.FAILED)
        logging.info(f"Result received for job: {result.jobId}")

    def checkWorkerHeartbeats(self):
        while self.running:
            currentTime = time.time()
            for workerId, worker in list(self.workers.items()):
                if currentTime - worker.lastHeartbeat > 60:  # 60 seconds timeout
                    logging.warning(f"Worker {workerId} timed out. Removing from active workers.")
                    del self.workers[workerId]
            time.sleep(10)

if __name__ == "__main__":
    manager = ManagerNode("0.0.0.0", 5000)
    manager.start()