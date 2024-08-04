import socket
import json
import subprocess
import threading
import time
import sys
import os


class Worker:
    def __init__(self, manager_host, manager_port):
        self.manager_host = manager_host
        self.manager_port = manager_port
        self.socket = None
        self.script_dir = os.path.join(os.path.dirname(__file__), "..", "worker_scripts")
        os.makedirs(self.script_dir, exist_ok=True)

    def start(self):
        while True:
            try:
                print(f"Attempting to connect to manager at {self.manager_host}:{self.manager_port}")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.manager_host, self.manager_port))
                print(f"Connected to manager. Sending registration request.")
                self.socket.send(json.dumps({'type': 'worker_register'}).encode())
                print("Registration request sent. Waiting for jobs...")

                threading.Thread(target=self.send_heartbeat, daemon=True).start()

                while True:
                    data = self.socket.recv(1024).decode()
                    if not data:
                        print("Connection to manager lost. Reconnecting...")
                        break
                    message = json.loads(data)
                    print(f"Received message from manager: {message['type']}")

                    if message['type'] == 'job':
                        print(f"Received job {message['job_id']}. Processing...")
                        script_path = self.save_script(message['job_id'], message['script_content'])
                        result = self.execute_job(script_path, message['args'])
                        self.socket.send(json.dumps(
                            {'type': 'worker_result', 'job_id': message['job_id'], 'result': result}).encode())
                        print(f"Job {message['job_id']} completed. Result sent to manager.")
            except Exception as e:
                print(f"Error: {e}. Attempting to reconnect in 5 seconds...")
                time.sleep(5)
            finally:
                if self.socket:
                    self.socket.close()

    def send_heartbeat(self):
        while True:
            try:
                self.socket.send(json.dumps({'type': 'heartbeat'}).encode())
                time.sleep(10)  # Send heartbeat every 10 seconds
            except:
                break

    def save_script(self, job_id, script_content):
        script_name = f"job_{job_id}.py"
        script_path = os.path.join(self.script_dir, script_name)
        with open(script_path, 'w') as f:
            f.write(script_content)
        print(f"Script for job {job_id} saved to {script_path}")
        return script_path

    def execute_job(self, script_path, args):
        try:
            # Use sys.executable to get the path of the current Python interpreter
            result = subprocess.run([sys.executable, script_path] + args, capture_output=True, text=True, timeout=60)
            return {'status': 'success', 'output': result.stdout, 'error': result.stderr}
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'error': 'Job exceeded 60 seconds timeout'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Worker Node')
    parser.add_argument('manager_host', type=str, help='Manager host address')
    parser.add_argument('manager_port', type=int, help='Manager port')
    args = parser.parse_args()

    worker = Worker(args.manager_host, args.manager_port)
    worker.start()
