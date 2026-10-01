# 🚀 CleanLoop AWS EC2 Deployment Module

This directory contains the continuous deployment (CD) automation scripts and systemd unit files for CleanLoop's AWS EC2 instance.

For the complete architectural guide, Mermaid diagram, and step-by-step execution walkthrough, please read:

👉 **[DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)**

---

## Files Overview
- `deploy.sh` — Bash deployment script (git pull, migrate, collectstatic, gunicorn & nginx restart).
- `smartwaste-deploy.service` — Systemd service runner.
- `smartwaste-deploy.timer` — Systemd 5-minute automated polling timer.
