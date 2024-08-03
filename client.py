#!/usr/bin/env python3

import socket
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def send_receive(host, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(json.dumps(message).encode())
        return json.loads(s.recv(1024).decode())


def submit_job(host, port, script_path, args):
    with open(script_path, 'r') as f:
        script_content = f.read()

    message = {
        'type': 'client_submit',
        'script_content': script_content,
        'args': args
    }
    response = send_receive(host, port, message)
    return response.get('job_id')


def get_result(host, port, job_id):
    message = {
        'type': 'client_result',
        'job_id': job_id
    }
    return send_receive(host, port, message)


def main():
    if len(sys.argv) < 5:
        print("Usage:")
        print("  python client.py submit <host> <port> <script_path> [args...]")
        print("  python client.py result <host> <port> <job_id>")
        sys.exit(1)

    action = sys.argv[1]
    host = sys.argv[2]
    port = int(sys.argv[3])

    if action == 'submit':
        script_path = sys.argv[4]
        args = sys.argv[5:]
        job_id = submit_job(host, port, script_path, args)
        print(f"Job submitted with ID: {job_id}")
    elif action == 'result':
        job_id = int(sys.argv[4])
        result = get_result(host, port, job_id)
        print("Result:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
