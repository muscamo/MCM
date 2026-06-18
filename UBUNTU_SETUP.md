# Ubuntu Server Setup Guide - Media Center Project

Complete step-by-step guide from fresh Ubuntu installation to full production deployment.

## Phase 1: Initial Server Setup

### 1.1 Update System
```bash
# Update package list and upgrade all packages
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget git vim htop tree unzip
```

### 1.2 Set Timezone
```bash
sudo timedatectl set-timezone UTC
# Or your preferred timezone
sudo timedatectl set-timezone Africa/Harare
```

### 1.3 Configure Hostname
```bash
sudo hostnamectl set-hostname media-center
# Edit hosts file
sudo vim /etc/hosts
# Add: 127.0.1.1 media-center
```

### 1.4 Create Deploy User (Optional but Recommended)
```bash
# Create new user for deployment
sudo adduser deploy
sudo usermod -aG sudo deploy

# Switch to deploy user
su - deploy
```

### 1.5 Configure SSH Key Authentication
```bash
# On your local machine, generate SSH key if you don't have one
ssh-keygen -t ed25519

# Copy public key to server
ssh-copy-id deploy@your-server-ip

# Disable password authentication (after testing SSH key login)
sudo vim /etc/ssh/sshd_config
# Change: PasswordAuthentication no
# Change: PubkeyAuthentication yes
sudo systemctl restart ssh
```

### 1.6 Configure Firewall
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

## Phase 2: Install Required Software

### 2.1 Install Python 3.14 and pip
```bash
# Add deadsnakes PPA for Python 3.14
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.14 and development tools
sudo apt install -y python3.14 python3.14-venv python3.14-dev python3-pip

# Set Python 3.14 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.14 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.14 1

# Verify installation
python3 --version
```

### 2.2 Install PostgreSQL
```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check status
sudo systemctl status postgresql
```

### 2.3 Install Nginx
```bash
# Install Nginx
sudo apt install -y nginx

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

### 2.4 Install Additional Dependencies
```bash
# Install system dependencies for Python packages
sudo apt install -y build-essential libpq-dev libssl-dev libffi-dev python3-setuptools

# Install certbot for SSL
sudo apt install -y certbot python3-certbot-nginx
```

## Phase 3: Database Setup

### 3.1 Create PostgreSQL Database and User
```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE media_center;
CREATE USER media_user WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE media_center TO media_user;
ALTER USER media_user WITH SUPERUSER;
\q
```

### 3.2 Configure PostgreSQL for Remote Connections (if needed)
```bash
# Edit PostgreSQL configuration
sudo vim /etc/postgresql/16/main/postgresql.conf
# Change: listen_addresses = 'localhost' to listen_addresses = '*'

sudo vim /etc/postgresql/16/main/pg_hba.conf
# Add at the end: host    all    all    127.0.0.1/32    md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

## Phase 4: Application Setup

### 4.1 Clone Repository
```bash
# Navigate to home directory
cd /home/deploy

# Clone your repository (replace with your actual repository)
git clone https://your-repository-url.git media-center
cd media-center
```

### 4.2 Create Python Virtual Environment
```bash
# Create virtual environment
python3.14 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 4.3 Install Python Dependencies
```bash
# Install requirements
pip install -r requirements.txt
```

### 4.4 Configure Environment Variables
```bash
# Copy production environment template
cp .env.production .env

# Edit .env with production values
vim .env
```

**Update these values in .env:**
```env
SECRET_KEY=generate-strong-random-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

DB_NAME=media_center
DB_USER=media_user
DB_PASSWORD=strong_password_here
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@your-domain.com

SITE_URL=https://your-domain.com
```

### 4.5 Generate Secret Key
```bash
# Generate a secure secret key
python3 -c 'import secrets; print(secrets.token_urlsafe(50))'
# Use the output for SECRET_KEY in .env
```

### 4.6 Run Database Migrations
```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4.7 Collect Static Files
```bash
# Collect static files for production
python manage.py collectstatic --noinput
```

### 4.8 Test Application
```bash
# Test run the application
python manage.py runserver 0.0.0.0:8000
# Press Ctrl+C to stop after testing
```

## Phase 5: Gunicorn Configuration

### 5.1 Create Gunicorn Systemd Service
```bash
# Create systemd service file
sudo vim /etc/systemd/system/media-center.service
```

**Add this content:**
```ini
[Unit]
Description=Media Center Django Application
After=network.target postgresql.service

[Service]
User=deploy
Group=www-data
WorkingDirectory=/home/deploy/media-center
Environment="PATH=/home/deploy/media-center/venv/bin"
ExecStart=/home/deploy/media-center/venv/bin/gunicorn media_center.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 3 \
    --threads 2 \
    --timeout 120 \
    --access-logfile /home/deploy/media-center/logs/gunicorn-access.log \
    --error-logfile /home/deploy/media-center/logs/gunicorn-error.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5.2 Create Logs Directory
```bash
# Create logs directory
mkdir -p /home/deploy/media-center/logs
chown -R deploy:www-data /home/deploy/media-center/logs
```

### 5.3 Enable and Start Gunicorn Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable media-center

# Start the service
sudo systemctl start media-center

# Check status
sudo systemctl status media-center

# View logs if needed
sudo journalctl -u media-center -f
```

## Phase 6: Nginx Configuration

### 6.1 Create Nginx Configuration
```bash
# Create Nginx configuration file
sudo vim /etc/nginx/sites-available/media-center
```

**Add this content:**
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /home/deploy/media-center/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/deploy/media-center/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 6.2 Enable Nginx Site
```bash
# Create symbolic link to enable site
sudo ln -s /etc/nginx/sites-available/media-center /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 6.3 Set File Permissions
```bash
# Set proper ownership and permissions
sudo chown -R deploy:www-data /home/deploy/media-center
sudo chmod -R 755 /home/deploy/media-center
sudo chmod -R 775 /home/deploy/media-center/media
sudo chmod -R 775 /home/deploy/media-center/staticfiles
```

## Phase 7: SSL Certificate Setup

### 7.1 Obtain SSL Certificate
```bash
# Obtain SSL certificate using Let's Encrypt
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Follow the prompts to enter email and agree to terms
```

### 7.2 Test SSL Certificate Renewal
```bash
# Test automatic renewal
sudo certbot renew --dry-run
```

### 7.3 Verify SSL Configuration
```bash
# Check Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

## Phase 8: Security Hardening

### 8.1 Configure Fail2Ban
```bash
# Install Fail2Ban
sudo apt install -y fail2ban

# Create local configuration
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Edit configuration
sudo vim /etc/fail2ban/jail.local

# Enable and start Fail2Ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 8.2 Configure Automatic Security Updates
```bash
# Install unattended-upgrades
sudo apt install -y unattended-upgrades

# Configure automatic updates
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 8.3 Secure PostgreSQL
```bash
# Edit PostgreSQL configuration to restrict connections
sudo vim /etc/postgresql/16/main/pg_hba.conf

# Ensure only local connections are allowed
# Comment out any lines that allow remote connections
```

## Phase 9: Monitoring and Maintenance

### 9.1 Set Up Log Rotation
```bash
# Create logrotate configuration for Gunicorn logs
sudo vim /etc/logrotate.d/media-center
```

**Add this content:**
```
/home/deploy/media-center/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deploy www-data
    sharedscripts
    postrotate
        systemctl reload media-center
    endscript
}
```

### 9.2 Set Up Database Backups
```bash
# Create backup script
sudo vim /usr/local/bin/backup-media-center.sh
```

**Add this content:**
```bash
#!/bin/bash
# Database backup script
BACKUP_DIR="/home/deploy/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U media_user media_center > $BACKUP_DIR/media_center_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /home/deploy/media-center/media/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

```bash
# Make script executable
sudo chmod +x /usr/local/bin/backup-media-center.sh

# Add to crontab for daily backups at 2 AM
crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-media-center.sh
```

### 9.3 Monitoring Commands
```bash
# Check application status
sudo systemctl status media-center

# Check Nginx status
sudo systemctl status nginx

# Check PostgreSQL status
sudo systemctl status postgresql

# View application logs
sudo journalctl -u media-center -f

# View Nginx access logs
sudo tail -f /var/log/nginx/access.log

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

## Phase 10: Final Testing

### 10.1 Test Application Access
```bash
# Test HTTP access
curl http://your-domain.com

# Test HTTPS access
curl https://your-domain.com

# Test from local machine
# Open browser and navigate to https://your-domain.com
```

### 10.2 Test Admin Panel
```bash
# Access admin panel at https://your-domain.com/admin
# Login with superuser credentials created earlier
```

### 10.3 Test Email Notifications
```bash
# Create a test notification through the application
# Verify email is received
```

## Phase 11: Deployment Checklist

Before going live, verify:

- [ ] Ubuntu server is fully updated
- [ ] Firewall is configured and enabled
- [ ] SSH key authentication is working
- [ ] Python 3.14 is installed and working
- [ ] PostgreSQL is running and database is created
- [ ] Application code is deployed
- [ ] Virtual environment is created and dependencies installed
- [ ] Environment variables are configured correctly
- [ ] Database migrations have been run
- [ ] Static files have been collected
- [ ] Gunicorn service is running
- [ ] Nginx is configured and running
- [ ] SSL certificate is installed and valid
- [ ] Application is accessible via HTTPS
- [ ] Email notifications are working
- [ ] Database backups are scheduled
- [ ] Log rotation is configured
- [ ] Monitoring is set up

## Troubleshooting

### Application won't start
```bash
# Check Gunicorn logs
sudo journalctl -u media-center -n 50

# Check if port 8000 is in use
sudo netstat -tlnp | grep 8000

# Test Gunicorn manually
cd /home/deploy/media-center
source venv/bin/activate
gunicorn media_center.wsgi:application --bind 127.0.0.1:8000
```

### Database connection errors
```bash
# Test PostgreSQL connection
sudo -u postgres psql -d media_center

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-16-main.log
```

### Static files not loading
```bash
# Check static files directory
ls -la /home/deploy/media-center/staticfiles/

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Re-collect static files
cd /home/deploy/media-center
source venv/bin/activate
python manage.py collectstatic --noinput
```

### Permission issues
```bash
# Fix permissions
sudo chown -R deploy:www-data /home/deploy/media-center
sudo chmod -R 755 /home/deploy/media-center
sudo chmod -R 775 /home/deploy/media-center/media
```

## Maintenance Commands

### Update Application
```bash
cd /home/deploy/media-center
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart media-center
```

### Restart Services
```bash
# Restart application
sudo systemctl restart media-center

# Restart Nginx
sudo systemctl restart nginx

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Check Disk Space
```bash
df -h
du -sh /home/deploy/media-center/*
```

## Support

For issues or questions, check:
- Application logs: `sudo journalctl -u media-center -f`
- Nginx logs: `sudo tail -f /var/log/nginx/error.log`
- PostgreSQL logs: `sudo tail -f /var/log/postgresql/postgresql-16-main.log`
