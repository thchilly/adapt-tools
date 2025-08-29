# Adapt Tools Deployment Guide

This document provides step-by-step instructions for deploying the Adapt Tools platform on a fresh VPS using Docker Compose. It covers prerequisites, setup, configuration, and best practices for a secure and reliable production deployment.

---

## 1. Prerequisites

- **VPS Sizing:** Minimum 2 vCPU, 2GB RAM (4GB recommended for larger datasets). At least 20GB disk space.
- **Operating System:** Ubuntu 22.04 LTS or similar (Debian, etc.).
- **Domain Name & DNS:** Point your domain or subdomain (e.g., `tools.example.com`) to your VPS IP with an A record.

---

## 2. Server Setup

1. **Connect via SSH:**
   ```sh
   ssh root@your.server.ip
   ```

2. **Update System:**
   ```sh
   apt update && apt upgrade -y
   ```

3. **(Recommended for 2GB RAM) Add Swap:**
   ```sh
   fallocate -l 2G /swapfile
   chmod 600 /swapfile
   mkswap /swapfile
   swapon /swapfile
   echo '/swapfile none swap sw 0 0' >> /etc/fstab
   ```

---

## 3. Install Docker & Docker Compose

```sh
apt install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Verify installation:
```sh
docker --version
docker compose version
```

---

## 4. Clone the Repository and Configure Environment

```sh
git clone https://github.com/YOUR_ORG/adapt-tools.git
cd adapt-tools
```

Copy the example environment file and edit as needed:
```sh
cp .env.example .env
nano .env
# (Set secrets, DB passwords, etc.)
```

---

## 5. Start the Stack

From the project root directory (where `docker-compose.yml` is located):
```sh
docker compose up -d --build
```

---

## 6. Verify Services

- **Streamlit App:** http://your.server.ip:8501
- **Static Assets:** http://your.server.ip/assets
- **phpMyAdmin:** http://your.server.ip:8081

If using a domain, replace `your.server.ip` with your domain.

---

## 7. Import Data from Excel

To import your main Excel master file:
```sh
docker compose exec app python3 import_excel.py /app/data/master/db_ready_master_cca_tools.xlsx
```

(Adjust the path if your file is different.)

**Optional:** If you don’t have a master Excel file, you can seed with sample data:
```sh
docker compose exec app python3 import_excel.py /app/data/sample/sample_data.xlsx
```

---

## 8. HTTPS Setup (Recommended)

You have two main options:

### Option A: Host-level Nginx Reverse Proxy + Let’s Encrypt

1. Install Nginx and Certbot:
   ```sh
   apt install nginx certbot python3-certbot-nginx
   ```
2. Configure Nginx as a reverse proxy for ports 80/443 to your app and assets. Example:
   ```
   server {
       listen 80;
       server_name tools.example.com;
       location / {
           proxy_pass http://localhost:8501;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       location /assets/ {
           proxy_pass http://localhost:80/assets/;
       }
   }
   ```
3. Obtain a certificate:
   ```sh
   certbot --nginx -d tools.example.com
   ```

### Option B: Caddy for Automatic HTTPS

1. Install Caddy (see https://caddyserver.com/docs/install).
2. Simple Caddyfile:
   ```
   tools.example.com {
       reverse_proxy localhost:8501
       handle_path /assets/* {
           reverse_proxy localhost:80
       }
   }
   ```
3. Start Caddy; it will manage HTTPS certificates automatically.

---

## 9. Production Hardening Tips

- **Firewall:** Use `ufw` to allow only necessary ports (80, 443, SSH).
- **phpMyAdmin:** Restrict access with HTTP basic auth or limit by IP.
- **MySQL Tuning:** For larger datasets, adjust `my.cnf` (e.g., buffer pool size).
- **Backups:** Automate MySQL dumps:
  ```sh
  docker compose exec db mysqldump -u root -pYOURPASSWORD YOUR_DB > backup.sql
  ```
- **Log Rotation:** Ensure Docker and app logs are rotated to prevent disk fill-up.

---

## 10. Maintenance Tasks

- **Upgrade Code:** Pull latest changes and rebuild:
  ```sh
  git pull
  docker compose up -d --build
  ```
- **Rotate Backups:** Regularly backup DB and `.env` file; test restores.
- **Update Docker Images:** Run `docker compose pull` and restart stack.

---

## 11. Troubleshooting

- **Check Logs:**
  ```sh
  docker compose logs
  ```
- **List Running Containers:**
  ```sh
  docker compose ps
  ```
- **Check Volume Mounts:**
  ```sh
  docker inspect <container>
  ```
- **Check Environment Variables:**
  ```sh
  docker compose exec app printenv
  ```
- **Common Issues:**
  - Port conflicts: Ensure ports 80, 443, 8501, 8081 are available.
  - Permissions: Ensure files in `data/` are readable by Docker containers.
  - Database errors: Check DB container logs and credentials in `.env`.

---

For further help, see the project README or open an issue.