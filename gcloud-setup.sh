# Set your project ID
PROJECT_ID="prj-snek-dev"
gcloud config set project $PROJECT_ID

echo "Creating microcluster VPC network..."

# Create a VPC network
gcloud compute networks create microcluster-network --subnet-mode=auto

# Create firewall rules to allow internal communication and SSH
gcloud compute firewall-rules create microcluster-allow-internal \
    --network microcluster-network \
    --allow tcp,udp,icmp \
    --source-ranges 10.0.0.0/8

gcloud compute firewall-rules create microcluster-allow-ssh \
    --network microcluster-network \
    --allow tcp:22 \
    --source-ranges 0.0.0.0/0

echo "microcluster network creation complete"
echo "Creating microcluster machines..."

# Create 3 VMs: 1 manager and 2 workers
gcloud compute instances create manager-vm worker-vm-1 worker-vm-2 \
    --network microcluster-network \
    --subnet microcluster-network \
    --zone us-central1-a \
    --machine-type e2-micro \
    --image-family ubuntu-2004-lts \
    --image-project ubuntu-os-cloud

echo "Machine creation complete"

# Get the internal IP of the manager VM
MANAGER_IP=$(gcloud compute instances describe manager-vm --zone us-central1-a \
    --format='get(networkInterfaces[0].networkIP)')

echo "IP address for Manager Node: ${MANAGER_IP}"

echo "Starting microcluster service..."

# SSH into each VM and set up the environment
for VM in manager-vm worker-vm-1 worker-vm-2; do
    gcloud compute ssh $VM --zone us-central1-a --command "
        sudo apt-get update && sudo apt-get install -y python3-pip git
        git clone https://github.com/snek-git/microcluster.git
        "
done

# Start the manager on manager-vm
gcloud compute ssh manager-vm --zone us-central1-a --command "
    cd microcluster
    python3 run.py manager 0.0.0.0 5001 > manager.log 2>&1 &
"

# Start workers on worker VMs
for WORKER in worker-vm-1 worker-vm-2; do
    gcloud compute ssh $WORKER --zone us-central1-a --command "
        cd microcluster
        python3 run.py worker $MANAGER_IP 5001 > worker.log 2>&1 &
    "
done

echo"microcluster service started"

# Clean up (uncomment these lines when you're done testing)
# gcloud compute instances delete manager-vm worker-vm-1 worker-vm-2 --zone us-central1-a --quiet
# gcloud compute firewall-rules delete microcluster-allow-internal microcluster-allow-ssh --quiet
# gcloud compute networks delete microcluster-network --quiet