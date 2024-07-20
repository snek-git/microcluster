# client.py
import socket
import json
import uuid
from utilities import Task, Result, TaskType, serialize, deserialize


class Client:
    def __init__(self, manager_host, manager_port):
        self.manager_host = manager_host
        self.manager_port = manager_port
        self.user_id = str(uuid.uuid4())

    def submit_task(self, task_type, content, args=None):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.manager_host, self.manager_port))
        client_socket.send(json.dumps({'type': 'client'}).encode())

        task = Task(str(uuid.uuid4()), self.user_id, task_type, content, args)
        message = {'action': 'submit_task', 'task': serialize(task)}
        client_socket.send(json.dumps(message).encode())

        response = json.loads(client_socket.recv(1024).decode())
        client_socket.close()
        return response['task_id']

    def get_result(self, task_id):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.manager_host, self.manager_port))
        client_socket.send(json.dumps({'type': 'client'}).encode())

        message = {'action': 'get_result', 'task_id': task_id}
        client_socket.send(json.dumps(message).encode())

        result_data = client_socket.recv(1024).decode()
        client_socket.close()
        return deserialize(result_data, Result)


if __name__ == "__main__":
    client = Client("localhost", 5000)

    # Submit a shell script task
    shell_task_id = client.submit_task(TaskType.SHELL_SCRIPT, "echo 'Hello, World!'")
    print(f"Submitted shell task: {shell_task_id}")

    # Submit a Python function task
    python_task_id = client.submit_task(TaskType.PYTHON_FUNCTION, "math.sqrt", [16])
    print(f"Submitted Python task: {python_task_id}")

    # Submit an executable task
    executable_task_id = client.submit_task(TaskType.EXECUTABLE, "/usr/bin/ls", ["-l"])
    print(f"Submitted executable task: {executable_task_id}")

    # Get results
    for task_id in [shell_task_id, python_task_id, executable_task_id]:
        result = client.get_result(task_id)
        print(f"Task {task_id} result: {result.output if result.success else result.error}")