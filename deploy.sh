#!/bin/bash
set -e

IP="65.21.152.243"
REPO_URL="https://github.com/obzorik/latlug-website.git"

echo "[DEPLOY] Pulling latest LatLUG website..."

# SSH to server and pull latest code
ssh -o StrictHostKeyChecking=no root@$IP "
  cd /app/latlug
  git pull origin main
  echo '[DEPLOY] Code updated'
"

echo "[DEPLOY] Restarting latlug service..."
ssh -o StrictHostKeyChecking=no root@$IP "
  systemctl restart latlug
  sleep 2
  systemctl status latlug --no-pager | head -5
  echo '[DEPLOY] Service restarted'
"

echo "✅ LatLUG deployed successfully!"
echo "🌐 Available at: http://studsup.eu/latlug-demo"
