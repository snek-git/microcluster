# microcluster - WIP

Microcluster is a distributed computing system for running Python scripts across multiple machines.

## what you can do with microcluster

- submit Python jobs from a client
- job is submitted to a main controller node, which then distributes jobs among the worker nodes
- retrieve job results


## Usage

For running on localhost with port 5000:

0. clone the repository:
   ```
   git clone https://github.com/yourusername/microcluster.git
   cd microcluster
   ```

1. Start the manager:
   ```
   python run.py manager
   ```

2. Start a worker node listening on port 5001:
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
