# worker_node.py
import socket
import json
import subprocess
import importlib
import sys
from utilities import Task, Result, TaskType, serialize, deserialize


def execute_task(task):
    try:
        if task.task_type == TaskType.SHELL_SCRIPT:
            output = subprocess.check_output(task.content, shell=True, stderr=subprocess.STDOUT, text=True)
            return Result(task.task_id, True, output)
        elif task.task_type == TaskType.PYTHON_FUNCTION:
            module_name, function_name = task.content.rsplit('.', 1)
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)
            output = function(*task.args)
            return Result(task.task_id, True, str(output))
        elif task.task_type == TaskType.EXECUTABLE:
            output = subprocess.check_output([task.content] + task.args, stderr=subprocess.STDOUT, text=True)
            return Result(task.task_id, True, output)
        else:
            return Result(task.task_id, False, None, "Unknown task type")
    except Exception as e:
        return Result(task.task_id, False, None, str(e))


class WorkerNode:
    def __init__(self, manager_host, manager_port):
        self.manager_host = manager_host
        self.manager_port = manager_port

    def start(self):
        worker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        worker_socket.connect((self.manager_host, self.manager_port))
        worker_socket.send(json.dumps({'type': 'worker'}).encode())

        while True:
            data = worker_socket.recv(1024).decode()
            if not data:
                break
            task = deserialize(data, Task)
            result = execute_task(task)
            worker_socket.send(serialize(result).encode())


if __name__ == "__main__":
    worker = WorkerNode("localhost", 5000)
    worker.start()