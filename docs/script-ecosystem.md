# Complete Script Ecosystem

This document provides an overview of the complete script ecosystem for Minikube deployment, testing, and cleanup.

## 📋 Script Overview

| Script | Purpose | Key Features |
|--------|---------|--------------|
| `deploy.sh` | Deploy all services with tunnels | Builds images, deploys to K8s, creates tunnels |
| `verify.sh` | Test all services via localhost | Tests endpoints, early exit on failure |
| `cleanup.sh` | Stop all services and tunnels | Removes everything, confirms cleanup |

## 🚀 Complete Workflow

### 1. Deploy Everything
```bash
./deploy.sh
```
**What it does**:
- Builds Docker images for frontend and backend
- Loads images into Minikube
- Deploys all Kubernetes services and deployments
- Starts tunnels for all services (frontend, Prometheus, Grafana)
- Captures tunnel URLs for later use
- Displays all localhost access URLs

**Output Example**:
```
✅ Deployment and tunnel setup complete!

=== Localhost Access URLs ===
  Frontend:      http://127.0.0.1:58711
  Prometheus:    http://127.0.0.1:30090
  Grafana:       http://127.0.0.1:30091 (admin/admin)
```

### 2. Verify Everything
```bash
./verify.sh
```
**What it does**:
- Detects tunnel URLs from deploy.sh output
- Tests all services via localhost tunnels
- Tests service endpoints and metrics
- Stops on first failure (early exit)
- Provides comprehensive status report

**Output Example**:
```
✅ All services verified successfully via localhost tunnels!

=== Localhost Access URLs ===
  Frontend:      http://127.0.0.1:58711
  Prometheus:    http://127.0.0.1:30090
  Grafana:       http://127.0.0.1:30091 (admin/admin)
```

### 3. Clean Up Everything (Optional)
```bash
./cleanup.sh
```
**What it does**:
- Stops all minikube service tunnels
- Removes tunnel URL files
- Deletes all Kubernetes services and deployments
- Deletes configuration resources
- Provides cleanup summary

**Output Example**:
```
✅ Cleanup complete!

=== Cleanup Summary ===
✅ Stopped all minikube service tunnels
✅ Removed tunnel URL files
✅ Deleted Kubernetes services and deployments
✅ Deleted configuration resources
```

## 🔄 Common Usage Patterns

### Development Workflow
```bash
# Deploy and test
./deploy.sh && ./verify.sh

# Make changes to code...

# Clean up and redeploy
./cleanup.sh --force && ./deploy.sh && ./verify.sh
```

### CI/CD Integration
```bash
#!/bin/bash
set -e

echo "Deploying services..."
./deploy.sh

echo "Verifying services..."
./verify.sh

echo "All tests passed!"
```

### Quick Reset
```bash
# Complete reset when things go wrong
./cleanup.sh --force
./deploy.sh
./verify.sh
```

### Interactive Development
```bash
# Deploy once
./deploy.sh

# Test multiple times during development
./verify.sh
./verify.sh
./verify.sh

# Clean up when done
./cleanup.sh
```

## 🛠️ Script Features

### deploy.sh Features
- ✅ **Docker Image Building**: Builds and loads images into Minikube
- ✅ **Kubernetes Deployment**: Deploys all services and monitoring stack
- ✅ **Automatic Tunnel Creation**: Starts tunnels for all services
- ✅ **URL Capture**: Stores tunnel URLs for later use
- ✅ **Process Management**: Manages background tunnel processes
- ✅ **Cleanup**: Removes existing tunnels before creating new ones

### verify.sh Features
- ✅ **Tunnel Detection**: Automatically finds tunnel URLs
- ✅ **Localhost Testing**: Tests only localhost connections
- ✅ **Early Exit**: Stops on first failure
- ✅ **Service Validation**: Tests all services and metrics
- ✅ **Status Reporting**: Clear success/failure feedback
- ✅ **URL Display**: Shows all accessible URLs

### cleanup.sh Features
- ✅ **Tunnel Cleanup**: Stops all minikube service tunnels
- ✅ **File Cleanup**: Removes tunnel URL and PID files
- ✅ **Service Deletion**: Deletes all Kubernetes resources
- ✅ **Resource Cleanup**: Removes configuration resources
- ✅ **Status Verification**: Checks for remaining resources
- ✅ **Confirmation Prompt**: Asks for confirmation (optional --force)

## 🔧 Advanced Usage

### Force Operations
```bash
# Force cleanup without confirmation
./cleanup.sh --force

# Force cleanup and redeploy
./cleanup.sh --force && ./deploy.sh
```

### Help and Information
```bash
# Show cleanup help
./cleanup.sh --help

# Check tunnel status manually
ps aux | grep "minikube service"

# Check Kubernetes resources
kubectl get all
```

### Troubleshooting
```bash
# If tunnels are stuck
pkill -f "minikube service"
./deploy.sh

# If services are in bad state
./cleanup.sh --force
./deploy.sh
./verify.sh

# If verification fails
./verify.sh  # Check which service failed
kubectl get pods  # Check pod status
kubectl logs <pod-name>  # Check logs
```

## 📊 Script Dependencies

### File Dependencies
- `deploy.sh` creates: `/tmp/*_tunnel_url_final.txt`
- `verify.sh` reads: `/tmp/*_tunnel_url_final.txt`
- `cleanup.sh` removes: `/tmp/*_tunnel_url*.txt`

### Process Dependencies
- `deploy.sh` starts: `minikube service` processes
- `verify.sh` tests: HTTP endpoints via tunnels
- `cleanup.sh` stops: All `minikube service` processes

### Kubernetes Dependencies
- `deploy.sh` creates: Services, deployments, configmaps
- `verify.sh` tests: Service endpoints and metrics
- `cleanup.sh` deletes: All created resources

## 🎯 Best Practices

### 1. Always Use the Scripts in Order
```bash
./deploy.sh    # Deploy first
./verify.sh    # Test second
./cleanup.sh   # Clean up last
```

### 2. Use Force Flag for Automation
```bash
# In scripts or CI/CD
./cleanup.sh --force
```

### 3. Check Exit Codes
```bash
./deploy.sh && echo "Deploy successful" || echo "Deploy failed"
./verify.sh && echo "All tests passed" || echo "Tests failed"
```

### 4. Monitor Resource Usage
```bash
# Check what's running
kubectl get all
ps aux | grep "minikube service"

# Clean up if needed
./cleanup.sh --force
```

## 🚨 Error Handling

### Common Issues and Solutions

**Tunnel Creation Fails**:
```bash
# Solution: Clean up and retry
./cleanup.sh --force
./deploy.sh
```

**Service Not Accessible**:
```bash
# Solution: Check tunnel status and redeploy
ps aux | grep "minikube service"
./deploy.sh
```

**Verification Fails**:
```bash
# Solution: Check logs and restart
kubectl get pods
kubectl logs <failing-pod>
./cleanup.sh --force && ./deploy.sh
```

**Port Conflicts**:
```bash
# Solution: Force cleanup
./cleanup.sh --force
./deploy.sh
```

## 📈 Benefits

### Before Script Ecosystem
- ❌ Manual Docker image building
- ❌ Manual Kubernetes deployment
- ❌ Manual tunnel management
- ❌ Manual service testing
- ❌ Manual cleanup procedures

### After Script Ecosystem
- ✅ **Single Command Deployment**: `./deploy.sh`
- ✅ **Single Command Testing**: `./verify.sh`
- ✅ **Single Command Cleanup**: `./cleanup.sh`
- ✅ **Automated Tunnel Management**: No manual intervention
- ✅ **Comprehensive Testing**: All services and endpoints tested
- ✅ **Clean Resource Management**: Proper cleanup and resource management

## 🎉 Summary

The complete script ecosystem provides:

1. **Seamless Deployment**: Single command deploys everything
2. **Reliable Testing**: Single command tests everything
3. **Clean Cleanup**: Single command cleans everything
4. **Automated Management**: No manual intervention required
5. **Comprehensive Coverage**: All services, tunnels, and resources managed

**Quick Start**:
```bash
./deploy.sh    # Deploy everything
./verify.sh    # Test everything
./cleanup.sh   # Clean everything
```

This ecosystem eliminates all the complexity of manual Minikube management and provides a production-ready development workflow! 🚀
