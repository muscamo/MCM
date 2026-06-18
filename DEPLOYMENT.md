# Production Deployment Guide

## Prerequisites
- PostgreSQL database
- Python 3.14+
- Domain name with SSL certificate
- Production server (Ubuntu, Debian, or similar)

## Environment Setup

### 1. Copy production environment file
```bash
cp .env.production .env
```

### 2. Update .env with production values
- Set `SECRET_KEY` to a strong random string
- Set `DEBUG=False`
- Set `ALLOWED_HOSTS` to your domain (e.g., `yourdomain.com,www.yourdomain.com`)
- Configure PostgreSQL credentials
- Configure email settings
- Set `SITE_URL` to your production domain

## Database Setup

### Create PostgreSQL database
```bash
sudo -u postgres psql
CREATE DATABASE media_center;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE media_center TO your_user;
\q
```

## Application Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Collect static files
```bash
python manage.py collectstatic --noinput
```

### 3. Run migrations
```bash
python manage.py migrate
```

### 4. Create superuser (if needed)
```bash
python manage.py createsuperuser
```

## Running with Gunicorn

### Start the application
```bash
gunicorn media_center.wsgi:application --bind 0.0.0.0:8000
```

### Recommended Gunicorn settings
```bash
gunicorn media_center.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

## Systemd Service (Recommended)

Create `/etc/systemd/system/media-center.service`:
```ini
[Unit]
Description=Media Center Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/project
Environment="PATH=/path/to/your/project/venv/bin"
ExecStart=/path/to/your/project/venv/bin/gunicorn media_center.wsgi:application --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable media-center
sudo systemctl start media-center
sudo systemctl status media-center
```

## Nginx Configuration

Create `/etc/nginx/sites-available/media-center`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/project/staticfiles/;
    }

    location /media/ {
        alias /path/to/your/project/media/;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/media-center /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Security Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use strong database password
- [ ] Enable SSL/HTTPS
- [ ] Configure firewall (allow only necessary ports)
- [ ] Keep system and dependencies updated
- [ ] Regular database backups
- [ ] Monitor logs for suspicious activity

## Backup Strategy

### Database backup
```bash
pg_dump media_center > backup_$(date +%Y%m%d).sql
```

### Media files backup
```bash
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/
```

## Monitoring

Check application logs:
```bash
sudo journalctl -u media-center -f
```

## Troubleshooting

### Permission issues
```bash
sudo chown -R www-data:www-data /path/to/your/project
sudo chmod -R 755 /path/to/your/project
```

### Database connection issues
- Verify PostgreSQL is running
- Check credentials in .env
- Ensure database exists and user has permissions

### Static files not loading
- Run `collectstatic` again
- Check file permissions
- Verify Nginx static file configuration
