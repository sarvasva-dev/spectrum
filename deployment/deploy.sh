#!/bin/bash
# Auto-deployment script for SmartWaste (EC2)

PROJECT_DIR="/home/ubuntu/spectrum"
VENV_DIR="/home/ubuntu/spectrum/venv"

echo "Starting deployment at $(date)"

# Go to project directory
cd $PROJECT_DIR || exit

# Stash any accidental local changes on server to prevent merge conflicts (except deploy.sh)
git stash push -- :!deployment/deploy.sh

# Pull latest code from GitHub
echo "Pulling latest code from Git..."
git pull origin main

# Activate virtual environment
source $VENV_DIR/bin/activate

# Install dependencies if requirements.txt changed
pip install -r requirements.txt

# Run migrations (using the new backend/ structure)
echo "Running migrations..."
cd backend
python manage.py makemigrations
python manage.py migrate

# Collect static files (if configured)
python manage.py collectstatic --noinput

# Restart Gunicorn service
echo "Restarting Gunicorn (smartwaste)..."
sudo systemctl restart smartwaste

# Reload Nginx
echo "Reloading Nginx..."
sudo systemctl reload nginx

echo "Deployment completed successfully at $(date)"
