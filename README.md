# microcluster

Microcluster is a minimal distributed computing system written in Python for running Python scripts across multiple machines.

## What you can do with microcluster

- Submit Python jobs from a client
- Jobs are submitted to a main controller node (manager), which then distributes them among worker nodes
- Retrieve job results


## Setup

For running on a distributed setup:

1. Clone the repository:
   ```
   git clone https://github.com/snek-git/microcluster.git
   cd microcluster
   ```

2. Start the manager:
   ```
   python3 run.py manager 0.0.0.0 5001
   ```

3. Start a worker node (run this on each worker machine):
   ```
   python3 run.py worker <manager_ip> 5001
   ```

## Job Submission and Result Retrieval

1. Submit a test script:
   ```
   python3 client.py submit <manager_ip> 5001 test_scripts/hello_world.py Alice
   ```
   This will return a job ID.

2. Get job results:
   ```
   python3 client.py result <manager_ip> 5001 <job_id>
   ```
   Replace `<job_id>` with the ID returned in step 1.

## Project Structure

- `manager_scripts/`: Directory where the manager stores received scripts
- `worker_scripts/`: Directory where workers store scripts before execution
- `test_scripts/`: Contains sample Python scripts for testing
- `src/`: Contains the core components (manager.py, worker.py)
- `client.py`: Client script for submitting jobs and retrieving results
- `run.py`: Script to start manager or worker nodes

## Notes

- Ensure that all machines can communicate over the specified port (default 5001)
- The system currently supports running Python scripts
- For testing on localhost, use `localhost` as the `<manager_ip>`

## License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.
