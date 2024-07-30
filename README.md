# microcluster - WIP

Microcluster is a distributed computing system for running Python scripts across multiple machines.

## Features

- Submit Python jobs from a client
- Distribute jobs to worker nodes
- Retrieve job results

## Setup

Before trying to run this program, ensure you have a version of Python 3.x on your machine.

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/microcluster.git
   cd microcluster
   ```

2. Set up a virtual environment (optional):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```


## Usage

For running on localhost:

1. Start the manager:
   ```
   python run.py manager
   ```

2. Start workers:
   ```
   python run.py worker localhost 5000 5001
   ```

3. Submit a test script:
   ```
   python cli/microcluster_client.py localhost 5000 submit --script ./test_scripts/test1.py --args arg1 arg2 arg3
   ```

4. Check job status:
   ```
   python cli/microcluster_client.py localhost 5000 state --jobId <job_id>
   ```

5. Get job results:
   ```
   python cli/microcluster_client.py localhost 5000 result --jobId <job_id>
   ```

## Project Structure

- `src/`: Core components (manager, worker, utilities)
- `cli/`: Client interface
- `test_scripts/`: Sample scripts
- `run.py`: Main entry point for manager and worker nodes

## License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.
