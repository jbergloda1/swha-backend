#!/bin/bash

# =====================================================================
# SWHA Backend Quick Deployment Script
# =====================================================================

set -e

echo "🚀 SWHA Backend Quick Deployment"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Get VM IP address
VM_IP=$(hostname -I | awk '{print $1}')
print_info "VM IP Address: $VM_IP"

# Step 1: Check prerequisites
print_info "Step 1: Checking prerequisites..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_warning "Docker not found. Installing Docker..."
    if [ -f "install-docker.sh" ]; then
        ./install-docker.sh
        print_info "Please log out and log back in, then run this script again"
        exit 0
    else
        print_error "install-docker.sh not found!"
        exit 1
    fi
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose not found!"
    print_info "Please run: ./install-docker.sh"
    exit 1
fi

# Check if user is in docker group
if ! groups $USER | grep &>/dev/null '\bdocker\b'; then
    print_warning "User $USER is not in docker group"
    print_info "Adding user to docker group..."
    sudo usermod -aG docker $USER
    print_warning "Please log out and log back in, then run this script again"
    exit 0
fi

print_status "Docker and Docker Compose are ready"

# Step 2: Environment configuration
print_info "Step 2: Configuring environment..."

if [ ! -f ".env" ]; then
    if [ -f "env.template" ]; then
        cp env.template .env
        print_status ".env file created from template"
        
        # Generate secure secret key
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
        
        # Generate secure passwords
        DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))" 2>/dev/null || openssl rand -base64 16)
        REDIS_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))" 2>/dev/null || openssl rand -base64 16)
        
        # Update .env file with secure values
        sed -i "s/your-secret-key-here-change-in-production/$SECRET_KEY/" .env
        sed -i "s/DEBUG=True/DEBUG=False/" .env
        sed -i "s/swha_password/$DB_PASSWORD/" .env
        sed -i "s/redis_password/$REDIS_PASSWORD/" .env
        
        # Add Docker-specific environment variables
        cat >> .env << EOF

# Docker deployment settings
DB_PASSWORD=$DB_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
HOST=0.0.0.0
PORT=8000

# Update CORS with VM IP
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost,http://$VM_IP
EOF
        
        print_status "Environment configured with secure defaults"
        print_info "Generated secure credentials and configured for VM IP: $VM_IP"
    else
        print_error "env.template not found!"
        exit 1
    fi
else
    print_status ".env file already exists"
fi

# Step 3: Create required directories
print_info "Step 3: Creating required directories..."
mkdir -p logs app/static/uploads app/static/audio app/static/videos nginx backups
print_status "Directories created"

# Step 4: Check for conflicts
print_info "Step 4: Checking for port conflicts..."

# Check port 80
if netstat -tuln 2>/dev/null | grep ':80 ' >/dev/null; then
    print_warning "Port 80 is already in use"
    print_info "Checking what's using port 80..."
    sudo netstat -tulpn | grep ':80 ' || true
    
    # Try to stop common web servers
    for service in apache2 nginx httpd; do
        if systemctl is-active --quiet $service 2>/dev/null; then
            print_info "Stopping $service..."
            sudo systemctl stop $service
            sudo systemctl disable $service
            print_status "$service stopped and disabled"
        fi
    done
fi

# Check port 8000
if netstat -tuln 2>/dev/null | grep ':8000 ' >/dev/null; then
    print_warning "Port 8000 is already in use"
    sudo netstat -tulpn | grep ':8000 ' || true
    print_warning "Please stop the service using port 8000 and try again"
fi

# Step 5: Deploy application
print_info "Step 5: Deploying SWHA Backend..."

# Stop any existing containers
docker-compose down 2>/dev/null || true

# Build and start services
print_info "Building and starting services..."
docker-compose up -d --build

print_status "Services deployment initiated"

# Step 6: Wait for services to be ready
print_info "Step 6: Waiting for services to be ready..."

# Wait for database
print_info "Waiting for database..."
timeout=60
count=0
while ! docker-compose exec -T db pg_isready -U swha_user -d swha_db 2>/dev/null; do
    echo -n "."
    sleep 2
    count=$((count + 1))
    if [ $count -gt $timeout ]; then
        print_error "Database failed to start within $timeout seconds"
        print_info "Check logs: ./deploy.sh logs db"
        exit 1
    fi
done
echo ""
print_status "Database is ready"

# Wait for Redis
print_info "Waiting for Redis..."
count=0
while ! docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; do
    echo -n "."
    sleep 2
    count=$((count + 1))
    if [ $count -gt $timeout ]; then
        print_error "Redis failed to start within $timeout seconds"
        print_info "Check logs: ./deploy.sh logs redis"
        exit 1
    fi
done
echo ""
print_status "Redis is ready"

# Wait for application
print_info "Waiting for application..."
count=0
while ! curl -f http://localhost:8000/health 2>/dev/null; do
    echo -n "."
    sleep 3
    count=$((count + 1))
    if [ $count -gt $timeout ]; then
        print_error "Application failed to start within $((timeout * 3)) seconds"
        print_info "Check logs: ./deploy.sh logs app"
        exit 1
    fi
done
echo ""
print_status "Application is ready"

# Wait for Nginx
print_info "Waiting for Nginx..."
count=0
while ! curl -f http://localhost/health 2>/dev/null; do
    echo -n "."
    sleep 2
    count=$((count + 1))
    if [ $count -gt $timeout ]; then
        print_error "Nginx failed to start within $timeout seconds"
        print_info "Check logs: ./deploy.sh logs nginx"
        exit 1
    fi
done
echo ""
print_status "Nginx is ready"

# Step 7: Final verification
print_info "Step 7: Final verification..."

# Test application endpoints
print_info "Testing application endpoints..."

# Health check
if curl -f http://localhost/health >/dev/null 2>&1; then
    print_status "Health check: OK"
else
    print_error "Health check: FAILED"
fi

# API documentation
if curl -f http://localhost/docs >/dev/null 2>&1; then
    print_status "API docs: OK"
else
    print_warning "API docs: Not accessible"
fi

# Check service status
print_info "Service status:"
docker-compose ps

echo ""
echo "🎉 SWHA Backend Deployment Complete!"
echo "=========================================="
print_status "All services are running successfully!"
echo ""
print_info "Access URLs:"
echo "  🌐 Main Application: http://localhost"
echo "  🌐 VM Access: http://$VM_IP"
echo "  📚 API Documentation: http://localhost/docs"
echo "  📖 ReDoc: http://localhost/redoc"
echo "  🔍 Health Check: http://localhost/health"
echo ""
print_info "Management commands:"
echo "  ./deploy.sh status    # Check service status"
echo "  ./deploy.sh logs      # View all logs"
echo "  ./deploy.sh logs app  # View application logs"
echo "  ./deploy.sh shell     # Open app shell"
echo "  ./deploy.sh down      # Stop all services"
echo ""
print_info "Testing endpoints:"
echo "  curl http://localhost/health"
echo "  curl http://localhost/docs"
echo "  curl http://localhost/api/v1/tts/voices"
echo ""

# Create a simple test script
cat > test-api.sh << 'EOF'
#!/bin/bash
echo "🧪 Testing SWHA Backend API..."

# Test health endpoint
echo "Testing health endpoint..."
curl -s http://localhost/health | jq . 2>/dev/null || curl -s http://localhost/health

echo -e "\n\nTesting API documentation..."
if curl -f http://localhost/docs >/dev/null 2>&1; then
    echo "✅ API docs accessible at http://localhost/docs"
else
    echo "❌ API docs not accessible"
fi

echo -e "\n\nTesting TTS voices endpoint..."
curl -s http://localhost/api/v1/tts/voices 2>/dev/null || echo "Note: This endpoint requires authentication"

echo -e "\n\nFor full API testing, visit: http://localhost/docs"
EOF

chmod +x test-api.sh
print_status "Created test-api.sh for API testing"

print_warning "Important Security Notes:"
echo "  1. Change default passwords in .env for production"
echo "  2. Configure proper domain names in CORS_ORIGINS"
echo "  3. Set up SSL/TLS for production use"
echo "  4. Regular backup: ./deploy.sh backup"
echo ""
print_info "For detailed documentation, see: DEPLOYMENT.md" 