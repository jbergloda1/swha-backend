#!/bin/bash

# =====================================================================
# SWHA Backend Docker Deployment Script
# =====================================================================

set -e  # Exit on any error

echo "🚀 SWHA Backend Docker Deployment"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed!"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found!"
    print_info "Creating .env file from template..."
    
    if [ -f "env.template" ]; then
        cp env.template .env
        print_status ".env file created from template"
        print_warning "Please edit .env file with your configuration before continuing!"
        print_info "Important settings to change:"
        echo "  - SECRET_KEY (generate a strong random key)"
        echo "  - DB_PASSWORD (change default database password)"
        echo "  - REDIS_PASSWORD (change default Redis password)"
        echo "  - AWS credentials (if using S3)"
        echo ""
        read -p "Press Enter after editing .env file..."
    else
        print_error "env.template not found!"
        exit 1
    fi
fi

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p logs
mkdir -p app/static/uploads
mkdir -p app/static/audio
mkdir -p app/static/videos
mkdir -p nginx
print_status "Directories created"

# Check if nginx configuration exists
if [ ! -f "nginx/nginx.conf" ] || [ ! -f "nginx/default.conf" ]; then
    print_error "Nginx configuration files not found!"
    print_info "Please ensure nginx/nginx.conf and nginx/default.conf exist"
    exit 1
fi

# Parse command line arguments
COMMAND=${1:-"up"}
ENVIRONMENT=${2:-"production"}

case $COMMAND in
    "build")
        print_info "Building Docker images..."
        docker-compose build --no-cache
        print_status "Docker images built successfully"
        ;;
    
    "up")
        print_info "Starting SWHA Backend services..."
        
        # Stop existing containers
        docker-compose down 2>/dev/null || true
        
        # Build and start services
        docker-compose up -d --build
        
        print_status "Services started successfully!"
        print_info "Waiting for services to be ready..."
        
        # Wait for database
        echo -n "Waiting for database"
        until docker-compose exec -T db pg_isready -U swha_user -d swha_db 2>/dev/null; do
            echo -n "."
            sleep 2
        done
        echo ""
        print_status "Database is ready"
        
        # Wait for Redis
        echo -n "Waiting for Redis"
        until docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; do
            echo -n "."
            sleep 2
        done
        echo ""
        print_status "Redis is ready"
        
        # Wait for application
        echo -n "Waiting for application"
        until curl -f http://localhost:8000/health 2>/dev/null; do
            echo -n "."
            sleep 3
        done
        echo ""
        print_status "Application is ready"
        
        # Wait for Nginx
        echo -n "Waiting for Nginx"
        until curl -f http://localhost/health 2>/dev/null; do
            echo -n "."
            sleep 2
        done
        echo ""
        print_status "Nginx is ready"
        
        echo ""
        print_status "🎉 SWHA Backend is now running!"
        echo ""
        print_info "Services available at:"
        echo "  🌐 Main Application: http://localhost"
        echo "  📚 API Documentation: http://localhost/docs"
        echo "  📖 ReDoc: http://localhost/redoc"
        echo "  🔍 Health Check: http://localhost/health"
        echo "  📊 Direct API: http://localhost:8000"
        echo ""
        print_info "Logs:"
        echo "  docker-compose logs -f          # All services"
        echo "  docker-compose logs -f app      # Application only"
        echo "  docker-compose logs -f nginx    # Nginx only"
        echo "  docker-compose logs -f db       # Database only"
        ;;
    
    "down")
        print_info "Stopping SWHA Backend services..."
        docker-compose down
        print_status "Services stopped"
        ;;
    
    "restart")
        print_info "Restarting SWHA Backend services..."
        docker-compose restart
        print_status "Services restarted"
        ;;
    
    "logs")
        SERVICE=${2:-""}
        if [ -n "$SERVICE" ]; then
            docker-compose logs -f $SERVICE
        else
            docker-compose logs -f
        fi
        ;;
    
    "shell")
        SERVICE=${2:-"app"}
        print_info "Opening shell in $SERVICE container..."
        docker-compose exec $SERVICE /bin/bash
        ;;
    
    "db-shell")
        print_info "Opening PostgreSQL shell..."
        docker-compose exec db psql -U swha_user -d swha_db
        ;;
    
    "backup")
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p $BACKUP_DIR
        
        print_info "Creating database backup..."
        docker-compose exec -T db pg_dump -U swha_user swha_db > $BACKUP_DIR/database.sql
        
        print_info "Creating static files backup..."
        tar -czf $BACKUP_DIR/static_files.tar.gz app/static/
        
        print_status "Backup created in $BACKUP_DIR"
        ;;
    
    "update")
        print_info "Updating SWHA Backend..."
        
        # Pull latest changes (if in git repo)
        if [ -d ".git" ]; then
            git pull
        fi
        
        # Rebuild and restart
        docker-compose build --no-cache
        docker-compose up -d
        
        print_status "Update completed"
        ;;
    
    "status")
        echo ""
        print_info "SWHA Backend Service Status:"
        echo "========================================"
        docker-compose ps
        echo ""
        
        print_info "Health Checks:"
        echo "========================================"
        
        # Check application health
        if curl -f http://localhost/health &>/dev/null; then
            print_status "Application: Healthy"
        else
            print_error "Application: Unhealthy"
        fi
        
        # Check database
        if docker-compose exec -T db pg_isready -U swha_user -d swha_db &>/dev/null; then
            print_status "Database: Healthy"
        else
            print_error "Database: Unhealthy"
        fi
        
        # Check Redis
        if docker-compose exec -T redis redis-cli ping &>/dev/null | grep -q PONG; then
            print_status "Redis: Healthy"
        else
            print_error "Redis: Unhealthy"
        fi
        ;;
    
    "cleanup")
        print_warning "This will remove all stopped containers, unused networks, and dangling images"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker system prune -f
            docker volume prune -f
            print_status "Cleanup completed"
        fi
        ;;
    
    *)
        echo "Usage: $0 {build|up|down|restart|logs|shell|db-shell|backup|update|status|cleanup}"
        echo ""
        echo "Commands:"
        echo "  build     - Build Docker images"
        echo "  up        - Start all services"
        echo "  down      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  logs      - Show logs (add service name for specific service)"
        echo "  shell     - Open shell in app container (or specify service)"
        echo "  db-shell  - Open PostgreSQL shell"
        echo "  backup    - Create backup of database and static files"
        echo "  update    - Update and restart services"
        echo "  status    - Show status and health checks"
        echo "  cleanup   - Clean up Docker resources"
        echo ""
        echo "Examples:"
        echo "  $0 up                    # Start all services"
        echo "  $0 logs app              # Show application logs"
        echo "  $0 shell db              # Open shell in database container"
        exit 1
        ;;
esac 