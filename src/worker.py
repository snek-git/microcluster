import socket
import json
import subprocess
import threading
import time
import sys


class Worker:
    def __init__(self, manager_host, manager_port):
        self.manager_host = manager_host
        self.manager_port = manager_port
        self.socket = None

    def start(self):
        while True:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.manager_host, self.manager_port))
                self.socket.send(json.dumps({'type': 'worker_register'}).encode())

                threading.Thread(target=self.send_heartbeat, daemon=True).start()

                while True:
                    data = self.socket.recv(1024).decode()
                    if not data:
                        break
                    message = json.loads(data)

                    if message['type'] == 'job':
                        result = self.execute_job(message['script'], message['args'])
                        self.socket.send(json.dumps(
                            {'type': 'worker_result', 'job_id': message['job_id'], 'result': result}).encode())
            except Exception as e:
                print(f"Error: {e}. Reconnecting...")
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

    def execute_job(self, script, args):
        try:
            # Use sys.executable to get the path of the current Python interpreter
            result = subprocess.run([sys.executable, script] + args, capture_output=True, text=True, timeout=60)
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
    