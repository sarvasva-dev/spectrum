# CleanLoop — Deployment Guide (Production / EC2)

This document provides step-by-step instructions for deploying CleanLoop on an Ubuntu/EC2 instance with Daphne (ASGI for WebSockets), Nginx, Systemd, and SSL (Certbot).

---

## 1. Prerequisites & Server Setup

- **OS**: Ubuntu 22.04 LTS / 24.04 LTS
- **Domain**: `cleanloop.sarthakml.in` / `www.cleanloop.sarthakml.in`
- **System Dependencies**:
  ```bash
  sudo apt update && sudo apt upgrade -y
  sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx git
  ```

---

## 2. Clone & Setup Virtual Environment

```bash
cd /var/www
sudo git clone https://github.com/sarvasva-dev/spectrum.git cleanloop
cd /var/www/cleanloop

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Environment Variables

Create `.env` file in `/var/www/cleanloop/.env`:

```env
DJANGO_SECRET_KEY=your-secure-random-secret-key
DJANGO_DEBUG=False
SARVAM_API_KEY=sk_bpnn5apo_Wmncfn6d2FMcjHbK2MugWYfX
```

---

## 4. Database & Static Files Setup

```bash
source venv/bin/activate
python backend/manage.py migrate
python backend/manage.py collectstatic --noinput
```

---

## 5. Systemd Service Setup

Create systemd service `/etc/systemd/system/cleanloop.service`:

```ini
[Unit]
Description=CleanLoop Daphne ASGI Application Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/cleanloop
ExecStart=/var/www/cleanloop/venv/bin/daphne -b 127.0.0.1 -p 8000 --root-path /var/www/cleanloop/backend smartwaste_project.asgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable & start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cleanloop
sudo systemctl start cleanloop
sudo systemctl status cleanloop
```

---

## 6. Nginx Reverse Proxy Setup

Create `/etc/nginx/sites-available/cleanloop`:

```nginx
server {
    server_name cleanloop.sarthakml.in www.cleanloop.sarthakml.in;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/cleanloop/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        alias /var/www/cleanloop/media/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable configuration & restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/cleanloop /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 7. SSL Certificate (Let's Encrypt / Certbot)

```bash
sudo certbot --nginx -d cleanloop.sarthakml.in -d www.cleanloop.sarthakml.in
```

---

## 8. Verification & Maintenance

Check logs:
```bash
sudo journalctl -u cleanloop -f
sudo tail -f /var/log/nginx/error.log
```

Redeploy script (`/var/www/cleanloop/deploy.sh`):
```bash
#!/bin/bash
set -e
cd /var/www/cleanloop
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python backend/manage.py migrate
python backend/manage.py collectstatic --noinput
sudo systemctl restart cleanloop
echo "CleanLoop updated successfully!"
```
