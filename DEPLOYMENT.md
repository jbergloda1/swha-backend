# 🚀 SWHA Backend Docker Deployment Guide

## 📋 Overview

This guide covers deploying the SWHA Backend using Docker containers on your VM. The deployment includes:

- 🐳 **FastAPI Application** - Main backend service
- 🗄️ **PostgreSQL Database** - Data persistence
- 🔄 **Redis Cache** - Session and caching
- 🌐 **Nginx Reverse Proxy** - Load balancing and static files

## 🔧 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ or Debian 11+
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: Minimum 10GB free space
- **CPU**: 2+ cores recommended

### Required Software
- Docker 20.10+
- Docker Compose 2.0+
- curl, git

## 🚀 Quick Start

### 1. Install Docker (if not installed)
```bash
# Run the installation script
cd swha-backend
chmod +x install-docker.sh
./install-docker.sh

# Log out and log back in to apply group changes
# Or run: newgrp docker
```

### 2. Configure Environment
```bash
# Copy environment template
cp env.template .env

# Edit configuration
nano .env
```

**Important settings to change:**
```env
# Security (CRITICAL!)
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars
DB_PASSWORD=your_secure_database_password
REDIS_PASSWORD=your_secure_redis_password

# Application
DEBUG=False
HOST=0.0.0.0
PORT=8000

# CORS (update with your domains)
CORS_ORIGINS=http://your-domain.com,https://your-domain.com

# S3 (optional)
USE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
S3_BUCKET_NAME=your-bucket-name
```

### 3. Deploy Application
```bash
# Make deploy script executable
chmod +x deploy.sh

# Deploy all services
./deploy.sh up
```

### 4. Verify Deployment
```bash
# Check service status
./deploy.sh status

# View logs
./deploy.sh logs

# Test application
curl http://localhost/health
```

## 📊 Service URLs

After successful deployment:

| Service | URL | Description |
|---------|-----|-------------|
| **Main Application** | http://localhost | Nginx reverse proxy |
| **API Documentation** | http://localhost/docs | Swagger UI |
| **ReDoc** | http://localhost/redoc | API documentation |
| **Health Check** | http://localhost/health | Service health |
| **Direct API** | http://localhost:8000 | Direct FastAPI access |

## 🛠️ Management Commands

### Basic Operations
```bash
# Start services
./deploy.sh up

# Stop services
./deploy.sh down

# Restart services
./deploy.sh restart

# Check status
./deploy.sh status

# View logs
./deploy.sh logs [service_name]
```

### Development & Debugging
```bash
# Open shell in app container
./deploy.sh shell

# Open database shell
./deploy.sh db-shell

# View specific service logs
./deploy.sh logs app
./deploy.sh logs nginx
./deploy.sh logs db
./deploy.sh logs redis
```

### Maintenance
```bash
# Create backup
./deploy.sh backup

# Update application
./deploy.sh update

# Clean up Docker resources
./deploy.sh cleanup
```

## 🔧 Configuration

### Environment Variables (.env)

#### Core Application Settings
```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Database
DATABASE_URL=postgresql://swha_user:password@db:5432/swha_db
DB_PASSWORD=your_secure_password

# Security
SECRET_KEY=your-super-secret-key-32-chars-minimum
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Redis
REDIS_PASSWORD=your_redis_password
```

#### S3 Integration (Optional)
```env
USE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=swha-audio-bucket
S3_PRESIGNED_URL_EXPIRY=3600
```

#### CORS Configuration
```env
# Update with your actual domains
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com,https://www.yourdomain.com
```

### Docker Compose Services

#### Application Service
- **Container**: `swha-app`
- **Port**: 8000
- **Health Check**: `/health` endpoint
- **Volumes**: Static files, logs

#### Database Service
- **Container**: `swha-db`
- **Port**: 5432
- **Volume**: `postgres_data`
- **Health Check**: `pg_isready`

#### Redis Service
- **Container**: `swha-redis`
- **Port**: 6379
- **Volume**: `redis_data`
- **Health Check**: `redis-cli ping`

#### Nginx Service
- **Container**: `swha-nginx`
- **Ports**: 80, 443
- **Volumes**: Static files, nginx config, logs

## 🔒 Security Considerations

### Essential Security Settings
1. **Change default passwords** in `.env`
2. **Generate strong SECRET_KEY**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. **Update CORS origins** with your actual domains
4. **Disable debug mode** in production (`DEBUG=False`)

### Nginx Security Headers
The nginx configuration includes:
- X-Frame-Options
- X-XSS-Protection
- X-Content-Type-Options
- Content-Security-Policy
- Rate limiting for API endpoints

### Network Security
- Services communicate via internal Docker network
- Only necessary ports exposed to host
- Database and Redis not directly accessible from internet

## 📊 Monitoring & Logs

### Log Locations
```bash
# Application logs
docker-compose logs -f app

# Nginx access/error logs
docker-compose logs -f nginx

# Database logs
docker-compose logs -f db

# All services
docker-compose logs -f
```

### Health Monitoring
```bash
# Quick health check
curl http://localhost/health

# Detailed status
./deploy.sh status

# Service-specific health
docker-compose ps
```

### Performance Monitoring
```bash
# Container resource usage
docker stats

# Service resource usage
docker-compose top
```

## 🔄 Backup & Recovery

### Create Backup
```bash
# Automated backup (database + static files)
./deploy.sh backup

# Manual database backup
docker-compose exec -T db pg_dump -U swha_user swha_db > backup.sql

# Manual static files backup
tar -czf static_backup.tar.gz app/static/
```

### Restore Backup
```bash
# Restore database
docker-compose exec -T db psql -U swha_user -d swha_db < backup.sql

# Restore static files
tar -xzf static_backup.tar.gz
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Container Won't Start
```bash
# Check logs for errors
./deploy.sh logs [service_name]

# Check container status
docker-compose ps

# Rebuild container
docker-compose build --no-cache [service_name]
```

#### 2. Database Connection Issues
```bash
# Check database health
docker-compose exec db pg_isready -U swha_user -d swha_db

# Check database logs
./deploy.sh logs db

# Reset database
docker-compose down -v
./deploy.sh up
```

#### 3. Permission Issues
```bash
# Fix static files permissions
sudo chown -R $USER:$USER app/static/
sudo chmod -R 755 app/static/
```

#### 4. Port Conflicts
```bash
# Check what's using port 80
sudo netstat -tulpn | grep :80

# Stop conflicting services
sudo systemctl stop apache2  # or nginx
```

### Service Health Checks

#### Application Health
```bash
curl -f http://localhost/health
# Should return: {"status": "healthy"}
```

#### Database Health
```bash
docker-compose exec db pg_isready -U swha_user -d swha_db
# Should return: accepting connections
```

#### Redis Health
```bash
docker-compose exec redis redis-cli ping
# Should return: PONG
```

## 🔄 Updates & Maintenance

### Update Application
```bash
# Pull latest changes (if using git)
git pull

# Update and restart
./deploy.sh update
```

### Update Dependencies
```bash
# Rebuild with latest base images
docker-compose build --no-cache --pull

# Restart services
./deploy.sh restart
```

### Regular Maintenance
```bash
# Clean up old Docker resources (weekly)
./deploy.sh cleanup

# Create backup (daily)
./deploy.sh backup

# Check disk usage
df -h
docker system df
```

## 🌐 Production Deployment

### Domain Setup
1. **Point domain to your VM's IP**
2. **Update CORS_ORIGINS in .env**
3. **Configure SSL/TLS** (recommended: Let's Encrypt)

### SSL Certificate (Optional)
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Performance Optimization
1. **Increase worker processes** in nginx config
2. **Tune PostgreSQL settings** based on available RAM
3. **Configure Redis persistence** based on needs
4. **Set up log rotation**

## 📞 Support

### Useful Commands Reference
```bash
# Deployment
./deploy.sh up|down|restart|build

# Monitoring  
./deploy.sh status|logs [service]

# Maintenance
./deploy.sh backup|update|cleanup

# Development
./deploy.sh shell [service]|db-shell

# Docker native commands
docker-compose ps               # Service status
docker-compose logs -f [service] # Live logs
docker-compose exec [service] bash # Shell access
docker system prune -f         # Cleanup
```

### Log Analysis
```bash
# Find errors in logs
./deploy.sh logs app | grep -i error

# Monitor real-time access
./deploy.sh logs nginx | grep -v health

# Database query logs
./deploy.sh logs db | grep -i slow
```

---

## 🎉 Success!

If everything is working correctly, you should be able to:
- ✅ Access API documentation at http://localhost/docs
- ✅ Get healthy response from http://localhost/health
- ✅ Use TTS API endpoints
- ✅ Use Lipsync API endpoints
- ✅ Upload and serve files
- ✅ Authenticate users

Happy deploying! 🚀 