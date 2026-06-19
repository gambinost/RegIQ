#!/usr/bin/env bash
# deploy_aws.sh — Build Docker image and deploy to EC2
# Usage: bash scripts/deploy_aws.sh ec2-user@<IP> ~/.ssh/key.pem
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Usage: $0 <ec2-host> <ssh-key-path>"
  echo "Example: $0 ec2-user@54.210.1.100 ~/.ssh/regiq-key.pem"
  exit 1
fi

EC2_HOST="$1"
SSH_KEY="$2"
REMOTE_DIR="~/regiq"

echo "=== RegIQ AWS Deploy ==="
echo "Target: $EC2_HOST"

# 1. Build Docker image locally
echo ""
echo "[1/4] Building Docker image..."
docker build -t regiq:latest .

# 2. Save image to tarball
echo ""
echo "[2/4] Saving Docker image..."
docker save regiq:latest | gzip > /tmp/regiq-image.tar.gz

# 3. Copy files to EC2
echo ""
echo "[3/4] Copying to EC2..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no /tmp/regiq-image.tar.gz "$EC2_HOST:$REMOTE_DIR/"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no docker-compose.yml "$EC2_HOST:$REMOTE_DIR/"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no .env "$EC2_HOST:$REMOTE_DIR/"

# 4. Load image and restart on EC2
echo ""
echo "[4/4] Loading image and starting container..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$EC2_HOST" bash -s <<'REMOTE'
set -e
cd ~/regiq
docker load < regiq-image.tar.gz
rm regiq-image.tar.gz
docker compose down 2>/dev/null || true
docker compose up -d
echo ""
echo "=== Deploy complete ==="
echo "App running at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
REMOTE

# Cleanup local tarball
rm -f /tmp/regiq-image.tar.gz

echo ""
echo "Done! Check: http://<your-ec2-public-ip>"
