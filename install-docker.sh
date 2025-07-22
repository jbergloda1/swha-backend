#!/bin/bash

# =====================================================================
# Docker Installation Script for Ubuntu/Debian
# =====================================================================

set -e

echo "🐳 Docker Installation Script"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please run this script as a regular user, not root"
    print_info "Use: bash install-docker.sh"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    print_error "Cannot detect OS version"
    exit 1
fi

print_info "Detected OS: $OS $VER"

# Check if Docker is already installed
if command -v docker &> /dev/null; then
    print_warning "Docker is already installed"
    docker --version
    DOCKER_INSTALLED=true
else
    DOCKER_INSTALLED=false
fi

# Check if Docker Compose is already installed
if command -v docker-compose &> /dev/null; then
    print_warning "Docker Compose is already installed"
    docker-compose --version
    COMPOSE_INSTALLED=true
else
    COMPOSE_INSTALLED=false
fi

if [ "$DOCKER_INSTALLED" = true ] && [ "$COMPOSE_INSTALLED" = true ]; then
    print_info "Both Docker and Docker Compose are already installed"
    print_info "Checking if user is in docker group..."
    
    if groups $USER | grep &>/dev/null '\bdocker\b'; then
        print_status "User $USER is already in docker group"
        exit 0
    else
        print_warning "User $USER is not in docker group"
        print_info "Adding user to docker group..."
        sudo usermod -aG docker $USER
        print_status "User added to docker group"
        print_warning "Please log out and log back in for changes to take effect"
        print_info "Or run: newgrp docker"
        exit 0
    fi
fi

# Install Docker if not installed
if [ "$DOCKER_INSTALLED" = false ]; then
    print_info "Installing Docker..."
    
    # Update package index
    print_info "Updating package index..."
    sudo apt-get update
    
    # Install prerequisites
    print_info "Installing prerequisites..."
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        apt-transport-https \
        software-properties-common
    
    # Add Docker's official GPG key
    print_info "Adding Docker GPG key..."
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Add Docker repository
    print_info "Adding Docker repository..."
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Update package index again
    sudo apt-get update
    
    # Install Docker Engine
    print_info "Installing Docker Engine..."
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin
    
    print_status "Docker installed successfully"
fi

# Install Docker Compose if not installed
if [ "$COMPOSE_INSTALLED" = false ]; then
    print_info "Installing Docker Compose..."
    
    # Get latest version
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    print_info "Installing Docker Compose version: $COMPOSE_VERSION"
    
    # Download and install
    sudo curl -L "https://github.com/docker/compose/releases/download/$COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Create symlink
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    print_status "Docker Compose installed successfully"
fi

# Add user to docker group
print_info "Adding user to docker group..."
sudo usermod -aG docker $USER

# Start and enable Docker service
print_info "Starting Docker service..."
sudo systemctl start docker
sudo systemctl enable docker

print_status "Docker service started and enabled"

# Verify installation
print_info "Verifying installation..."

# Test Docker
if sudo docker run hello-world &> /dev/null; then
    print_status "Docker is working correctly"
else
    print_error "Docker test failed"
fi

# Test Docker Compose
if docker-compose --version &> /dev/null; then
    print_status "Docker Compose is working correctly"
    docker-compose --version
else
    print_error "Docker Compose test failed"
fi

echo ""
print_status "🎉 Docker installation completed successfully!"
echo ""
print_warning "IMPORTANT: Please log out and log back in (or run 'newgrp docker')"
print_warning "to apply group changes before using Docker without sudo"
echo ""
print_info "Useful commands:"
echo "  docker --version              # Check Docker version"
echo "  docker-compose --version      # Check Docker Compose version"
echo "  docker run hello-world        # Test Docker installation"
echo "  sudo systemctl status docker  # Check Docker service status"
echo ""
print_info "Next steps:"
echo "  1. Log out and log back in"
echo "  2. Run: cd swha-backend && ./deploy.sh up"
echo "  3. Access your application at http://localhost" 