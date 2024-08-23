import socket
import json
import threading
import queue
import time
import os


class Manager:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.job_queue = queue.Queue()
        self.workers = {}
        self.job_results = {}
        self.lock = threading.Lock()
        self.script_dir = os.path.join(os.path.dirname(__file__), "..", "manager_scripts")
        os.makedirs(self.script_dir, exist_ok=True)

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', self.port))  # Bind to all interfaces
        server.listen(5)
        print(f"Manager listening on {self.host}:{self.port}")

        threading.Thread(target=self.check_worker_health, daemon=True).start()

        while True:
            client, addr = server.accept()
            print(f"New connection from: {addr}")
            threading.Thread(target=self.handle_connection, args=(client,)).start()

    def handle_connection(self, client):
        message = None
        try:
            data = client.recv(1024).decode()
            message = json.loads(data)

            if message['type'] == 'worker_register':
                self.register_worker(client)
            elif message['type'] == 'client_submit':
                self.handle_job_submission(client, message)
            elif message['type'] == 'client_result':
                self.handle_result_request(client, message)
            else:
                print(f"Unknown message type: {message['type']}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except KeyError as e:
            print(f"Missing key in message: {e}")
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            if message is None or message.get('type') != 'worker_register':
                client.close()

    def register_worker(self, client):
        worker_id = client.getpeername()
        print(f"Attempting to register worker: {worker_id}")
        with self.lock:
            self.workers[worker_id] = {'socket': client, 'last_heartbeat': time.time()}
        print(f"Worker registered successfully: {worker_id}")
        print(f"Current workers: {list(self.workers.keys())}")
        threading.Thread(target=self.handle_worker, args=(worker_id,)).start()

    def handle_worker(self, worker_id):
        worker = self.workers[worker_id]
        client = worker['socket']
        try:
            while True:
                data = client.recv(1024).decode()
                if not data:
                    break
                message = json.loads(data)

                if message['type'] == 'heartbeat':
                    with self.lock:
                        worker['last_heartbeat'] = time.time()
                elif message['type'] == 'worker_result':
                    self.job_results[message['job_id']] = message['result']
                    print(f"Job {message['job_id']} completed")
                    self.assign_job(worker_id)
        except Exception as e:
            print(f"Error handling worker {worker_id}: {e}")
        finally:
            with self.lock:
                if worker_id in self.workers:
                    del self.workers[worker_id]
            print(f"Worker disconnected: {worker_id}")

    def handle_job_submission(self, client, message):
        job_id = len(self.job_results) + 1
        script_content = message['script_content']
        script_name = f"job_{job_id}.py"
        script_path = os.path.join(self.script_dir, script_name)

        with open(script_path, 'w') as f:
            f.write(script_content)

        self.job_queue.put((job_id, script_path, message['args']))
        client.send(json.dumps({'job_id': job_id}).encode())
        print(f"Job {job_id} submitted and script saved to {script_path}")
        self.assign_job()

    def handle_result_request(self, client, message):
        job_id = message['job_id']
        if job_id in self.job_results:
            result = self.job_results[job_id]
            client.send(json.dumps(result).encode())
        else:
            client.send(json.dumps({'status': 'not_ready'}).encode())

    def assign_job(self, worker_id=None):
        print(f"Attempting to assign job. Queue size: {self.job_queue.qsize()}")
        if self.job_queue.empty():
            print("Job queue is empty. No job to assign.")
            return
        if not self.workers:
            print("No workers available. Cannot assign job.")
            return
        job = self.job_queue.get()
        if worker_id is None:
            worker_id = next(iter(self.workers))
        worker = self.workers[worker_id]

        print(f"Assigning job {job[0]} to worker {worker_id}")
        with open(job[1], 'r') as f:
            script_content = f.read()

        try:
            worker['socket'].send(json.dumps({
                'type': 'job',
                'job_id': job[0],
                'script_content': script_content,
                'args': job[2]
            }).encode())
            print(f"Job {job[0]} sent to worker {worker_id}")
        except Exception as e:
            print(f"Error sending job to worker: {e}")
            self.job_queue.put(job)  # Put the job back in the queue

    def check_worker_health(self):
        while True:
            time.sleep(10) 
            with self.lock:
                current_time = time.time()
                dead_workers = [worker_id for worker_id, worker in self.workers.items()
                                if current_time - worker['last_heartbeat'] > 30]
                for worker_id in dead_workers:
                    print(f"Worker {worker_id} is unresponsive. Removing.")
                    del self.workers[worker_id]
