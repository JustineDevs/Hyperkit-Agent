# Script Index

This directory contains automation scripts for development, deployment, and maintenance.

## 📜 Available Scripts

### **Development Scripts**
- **`install.sh`** - Installs dependencies and configures environment
- **`setup-dev.sh`** - Sets up development environment
- **`test.sh`** - Runs test suite with coverage
- **`lint.sh`** - Runs code quality checks

### **Deployment Scripts**
- **`deploy.sh`** - Deploys contracts or docs automatically
- **`build.sh`** - Builds the application for production
- **`release.sh`** - Creates and publishes releases

### **Maintenance Scripts**
- **`clean.sh`** - Cleans build artifacts and temporary files
- **`backup.sh`** - Creates backups of important data
- **`update.sh`** - Updates dependencies and configurations

## 🚀 Usage

### **Running Scripts**
```bash
# Make script executable
chmod +x scripts/script_name.sh

# Run script
./scripts/script_name.sh

# Run with specific options
./scripts/script_name.sh --option value
```

### **Development Workflow**
```bash
# Setup development environment
./scripts/setup-dev.sh

# Run tests
./scripts/test.sh

# Check code quality
./scripts/lint.sh

# Clean up
./scripts/clean.sh
```

### **Deployment Workflow**
```bash
# Build for production
./scripts/build.sh

# Deploy to staging
./scripts/deploy.sh --env staging

# Deploy to production
./scripts/deploy.sh --env production
```

## 📋 Script Guidelines

### **Script Requirements**
- Use `#!/bin/bash` shebang
- Include error handling with `set -e`
- Provide usage information with `--help`
- Use descriptive variable names
- Add comments for complex logic

### **Error Handling**
```bash
#!/bin/bash
set -e  # Exit on any error

# Function to handle errors
error_exit() {
    echo "Error: $1" >&2
    exit 1
}

# Usage information
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  --help    Show this help message"
    echo "  --env     Environment (dev|staging|prod)"
}
```

### **Logging**
```bash
# Log levels
LOG_LEVEL=${LOG_LEVEL:-INFO}

log_info() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

log_debug() {
    if [ "$LOG_LEVEL" = "DEBUG" ]; then
        echo "[DEBUG] $1"
    fi
}
```

## 🔧 Configuration

### **Environment Variables**
Scripts use environment variables for configuration:
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARN, ERROR)
- `ENVIRONMENT`: Target environment (dev, staging, prod)
- `PYTHON_PATH`: Python executable path
- `NODE_PATH`: Node.js executable path

### **Script Configuration**
Create `scripts/config.sh` for shared configuration:
```bash
#!/bin/bash
# Shared configuration for all scripts

# Default values
DEFAULT_ENV="dev"
DEFAULT_LOG_LEVEL="INFO"

# Load from environment or use defaults
ENVIRONMENT=${ENVIRONMENT:-$DEFAULT_ENV}
LOG_LEVEL=${LOG_LEVEL:-$DEFAULT_LOG_LEVEL}
```

## 📊 Monitoring

### **Script Execution**
- All scripts log execution time
- Error conditions are logged
- Success/failure status is tracked
- Performance metrics are collected

### **Health Checks**
```bash
# Check if service is running
check_service() {
    local service=$1
    if pgrep -f "$service" > /dev/null; then
        log_info "$service is running"
        return 0
    else
        log_error "$service is not running"
        return 1
    fi
}
```

## 🔄 Maintenance

### **Regular Tasks**
- Update dependencies monthly
- Review and update scripts quarterly
- Test scripts in all environments
- Document any changes

### **Script Testing**
```bash
# Test script functionality
./scripts/test-scripts.sh

# Validate script syntax
bash -n scripts/*.sh

# Check for common issues
shellcheck scripts/*.sh
```

## 📞 Support

### **Troubleshooting**
- Check script logs for errors
- Verify environment configuration
- Test with minimal options first
- Contact maintainers for issues

### **Contributing**
- Follow script guidelines
- Test in multiple environments
- Update documentation
- Submit pull requests for improvements
