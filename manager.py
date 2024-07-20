# manager_node.py
import socket
import threading
import queue
import json
from utilities import Task, serialize, deserialize


class ManagerNode:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.task_queue = queue.PriorityQueue()
        self.results = {}
        self.workers = []
        self.users = {}  # Dictionary to store user information
        self.user_tasks = {}  # Dictionary to store tasks per user

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Manager node listening on {self.host}:{self.port}")

        threading.Thread(target=self.distribute_tasks, daemon=True).start()

        while True:
            client_socket, addr = server_socket.accept()
            client_thread = threading.Thread(target=self.handle_connection, args=(client_socket, addr))
            client_thread.start()

    def handle_connection(self, client_socket, addr):
        data = client_socket.recv(1024).decode()
        message = json.loads(data)

        if message['type'] == 'worker':
            print(f"Worker node connected from {addr}")
            self.workers.append(client_socket)
        elif message['type'] == 'client':
            self.handle_client(client_socket)

    def handle_client(self, client_socket):
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            message = json.loads(data)
            if message['action'] == 'submit_task':
                task = deserialize(message['task'], Task)
                self.submit_task(task, client_socket)
            elif message['action'] == 'get_result':
                self.send_result(message['task_id'], client_socket)
        client_socket.close()

    def submit_task(self, task, client_socket):
        if task.user_id not in self.users:
            self.users[task.user_id] = {'tasks': []}
        self.users[task.user_id]['tasks'].append(task.task_id)
        priority = len(self.users[task.user_id]['tasks'])  # Simple priority based on number of user's tasks
        self.task_queue.put((priority, task))
        client_socket.send(serialize({'status': 'task_submitted', 'task_id': task.task_id}).encode())

    def send_result(self, task_id, client_socket):
        if task_id in self.results:
            result = self.results.pop(task_id)
            client_socket.send(serialize(result).encode())
        else:
            client_socket.send(serialize({'status': 'result_not_ready'}).encode())

    def distribute_tasks(self):
        while True:
            if not self.task_queue.empty() and self.workers:
                _, task = self.task_queue.get()
                worker = self.workers.pop(0)
                worker.send(serialize(task).encode())
                self.workers.append(worker)  # Move to the end of the list

    def receive_result(self, result):
        self.results[result.task_id] = result
        user_id = next(user_id for user_id, user_data in self.users.items() if result.task_id in user_data['tasks'])
        self.users[user_id]['tasks'].remove(result.task_id)


if __name__ == "__main__":
    manager = ManagerNode("localhost", 5000)
    manager.start()
