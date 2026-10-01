# 🚀 CleanLoop AWS EC2 Auto-Deployment Architecture Guide

This document provides a complete guide to the continuous deployment (CD) architecture used by CleanLoop on the AWS EC2 production instance. It details how the bash scripts and systemd timers work together to automatically deploy code updates directly from GitHub.

---

## 📐 Overall Deployment Architecture

```mermaid
graph TD
    Developer[Developer Push to GitHub main] --> GitHub[GitHub Repository sarvasva-dev/spectrum]
    
    subgraph AWS EC2 Instance (Ubuntu)
        Timer[Systemd Timer: smartwaste-deploy.timer] -->|Fires every 5 mins| Service[Systemd Service: smartwaste-deploy.service]
        Service -->|Executes| DeployScript[deployment/deploy.sh]
        
        DeployScript -->|1. git pull origin main| Code[Pull Latest Codebase]
        DeployScript -->|2. pip install| Venv[Python Virtualenv]
        DeployScript -->|3. makemigrations & migrate| DB[(SQLite db.sqlite3)]
        DeployScript -->|4. collectstatic| Static[Static Assets / staticfiles/]
        DeployScript -->|5. systemctl restart smartwaste| Gunicorn[Gunicorn / Daphne Application Server]
        DeployScript -->|6. systemctl reload nginx| Nginx[Nginx Reverse Proxy & SSL Web Server]
        
        Nginx -->|Proxy Pass 80/443 -> 8000| Gunicorn
    end
    
    Users[Citizens & Municipal Admins] -->|HTTPS Requests| Nginx
```

---

## 📁 File-by-File Breakdown (`deployment/`)

### 1. `deployment/deploy.sh` (Automated Deployment Execution Script)
* **Type**: Bash Shell Script
* **Purpose**: Performs all necessary steps on the EC2 instance to pull, build, migrate, collect assets, and restart application services.
* **Execution Flow**:
  1. `cd /home/ubuntu/spectrum` ➔ Navigates to project root directory.
  2. `git stash push -- :!deployment/deploy.sh` ➔ Stashes any server-side local temporary edits.
  3. `git pull origin main` ➔ Fetches latest committed code from GitHub.
  4. `source /home/ubuntu/spectrum/venv/bin/activate` ➔ Activates server Python virtual environment.
  5. `pip install -r requirements.txt` ➔ Installs any newly added Python packages.
  6. `cd backend && python manage.py makemigrations && python manage.py migrate` ➔ Updates database tables & schemas.
  7. `python manage.py collectstatic --noinput` ➔ Synchronizes static HTML/CSS/JS files for production serving.
  8. `sudo systemctl restart smartwaste` ➔ Restarts the Gunicorn/Daphne application server daemon.
  9. `sudo systemctl reload nginx` ➔ Gracefully reloads Nginx web server configuration.

---

### 2. `deployment/smartwaste-deploy.service` (Systemd Service Unit)
* **Type**: Systemd Service Unit File (`oneshot`)
* **Purpose**: Wraps `deploy.sh` as a system background service unit.
* **Configuration**:
  - `User=ubuntu` ➔ Runs under the standard EC2 deployment user.
  - `ExecStart=/bin/bash /home/ubuntu/spectrum/deployment/deploy.sh` ➔ Triggers the main deployment script.

---

### 3. `deployment/smartwaste-deploy.timer` (Systemd Timer Unit)
* **Type**: Systemd Timer Unit File
* **Purpose**: Acts as an automated cron-like scheduler for Continuous Deployment.
* **Configuration**:
  - `OnBootSec=5min` ➔ Starts 5 minutes after EC2 boot up.
  - `OnUnitActiveSec=5min` ➔ Triggers `smartwaste-deploy.service` every 5 minutes indefinitely.

---

## 🔄 How the Deployment Automation Works (End-to-End)

1. **Code Push**: Developer pushes bug fixes or features to the `main` branch on GitHub.
2. **Timer Trigger**: Every 5 minutes, `smartwaste-deploy.timer` fires `smartwaste-deploy.service`.
3. **Execution**: `smartwaste-deploy.service` executes `/home/ubuntu/spectrum/deployment/deploy.sh`.
4. **Git Sync**: `deploy.sh` pulls the new commit from `origin/main`.
5. **Database & Assets Sync**: Django migrations are applied to `db.sqlite3` and static assets are collected into `staticfiles/`.
6. **Live Service Reload**: `smartwaste` Gunicorn service is restarted and Nginx is reloaded.
7. **Result**: The production server at `https://cleanloop.sarthakml.in/` is updated live automatically without downtime or manual SSH commands!
