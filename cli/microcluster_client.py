#!/usr/bin/env python3

import sys
import os
import socket
import json
import argparse
import logging

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utilities import JobResult, serialize, deserialize

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class Client:
    def __init__(self, managerHost, managerPort):
        self.managerHost = managerHost
        self.managerPort = managerPort

    def submitJob(self, scriptPath, args=None):
        return self._sendReceive({'action': 'submit_job', 'scriptPath': scriptPath, 'args': args or []})

    def getResult(self, jobId):
        return self._sendReceive({'action': 'get_result', 'jobId': jobId})

    def getJobState(self, jobId):
        return self._sendReceive({'action': 'get_job_state', 'jobId': jobId})

    def _sendReceive(self, message):
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.settimeout(30)  # 30-second timeout
        try:
            clientSocket.connect((self.managerHost, self.managerPort))
            logging.info(f"Connected to manager at {self.managerHost}:{self.managerPort}")

            clientSocket.send(json.dumps({'type': 'client'}).encode() + b'\n')
            logging.info("Sent client type identifier")

            clientSocket.send(json.dumps(message).encode() + b'\n')
            logging.info(f"Sent message: {message}")

            response = clientSocket.recv(1024).decode().strip()
            logging.info(f"Received response: {response}")

            if not response:
                logging.error("Received empty response from manager")
                return None

            return json.loads(response)
        except socket.timeout:
            logging.error("Timeout waiting for manager response")
        except ConnectionRefusedError:
            logging.error(f"Connection refused. Is the manager running at {self.managerHost}:{self.managerPort}?")
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON response: {e}")
        except Exception as e:
            logging.error(f"Error communicating with manager: {str(e)}")
        finally:
            clientSocket.close()
        return None

def main():
    parser = argparse.ArgumentParser(description="Client for Distributed Computing Framework")
    parser.add_argument("managerHost", help="Manager host address")
    parser.add_argument("managerPort", type=int, help="Manager port")
    parser.add_argument("action", choices=["submit", "result", "state"], help="Action to perform")
    parser.add_argument("--script", help="Script path for job submission")
    parser.add_argument("--args", nargs="*", help="Arguments for the script")
    parser.add_argument("--jobId", help="Job ID for result or state query")

    args = parser.parse_args()

    client = Client(args.managerHost, args.managerPort)

    if args.action == "submit":
        if not args.script:
            print("Error: Script path is required for job submission")
            return
        response = client.submitJob(args.script, args.args)
        if response is None:
            print("Failed to submit job. Check the logs for more information.")
        elif response.get('status') == 'job_submitted':
            print(f"Job submitted with ID: {response['jobId']}")
        else:
            print(f"Unexpected response: {response}")

    elif args.action == "result":
        if not args.jobId:
            print("Error: Job ID is required for result query")
            return
        result = client.getResult(args.jobId)
        if result is None:
            print("Failed to get result. Check the logs for more information.")
        elif result.get('status') == 'result_not_ready':
            print(f"Result not ready for job {args.jobId}")
        elif result.get('status') == 'result_ready':
            job_result = deserialize(result['result'], JobResult)
            if job_result.success:
                print(f"Job {job_result.jobId} completed successfully:")
                print(job_result.output)
            else:
                print(f"Job {job_result.jobId} failed:")
                print(job_result.error)
        else:
            print(f"Unexpected result format: {result}")

    elif args.action == "state":
        if not args.jobId:
            print("Error: Job ID is required for state query")
            return
        state = client.getJobState(args.jobId)
        if state is None:
            print("Failed to get job state. Check the logs for more information.")
        else:
            print(f"State of job {args.jobId}: {state['state']}")

if __name__ == "__main__":
    main()