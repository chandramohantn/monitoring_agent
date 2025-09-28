# Deployment and Verification Guide

This guide explains how to use the enhanced `deploy.sh` and `verify.sh` scripts for seamless Minikube service deployment and testing.

## 🚀 Quick Start

### 1. Deploy All Services with Automatic Tunnels
```bash
./deploy.sh
```

This single command will:
- Build and deploy all services to Minikube
- Automatically start tunnels for all services (frontend, Prometheus, Grafana)
- Display all localhost access URLs
- Set up everything needed for local access

### 2. Verify All Services
```bash
./verify.sh
```

This single command will:
- Test all services via localhost tunnels
- Verify service endpoints and metrics
- Stop on first failure (early exit)
- Provide comprehensive status report

### 3. Clean Up Everything (Optional)
```bash
./cleanup.sh
```

This single command will:
- Stop all minikube service tunnels
- Remove tunnel URL files
- Delete all Kubernetes services and deployments
- Delete configuration resources
- Provide cleanup summary

## 📋 What Each Script Does

### deploy.sh - Complete Deployment Solution

**Features**:
- ✅ **Docker Image Building**: Builds backend and frontend images
- ✅ **Minikube Integration**: Loads images into Minikube
- ✅ **Kubernetes Deployment**: Deploys all services and monitoring stack
- ✅ **Automatic Tunnel Creation**: Starts tunnels for all services
- ✅ **URL Capture**: Captures and stores tunnel URLs
- ✅ **Process Management**: Manages background tunnel processes
- ✅ **Cleanup**: Removes existing tunnels before creating new ones

**Services Deployed**:
- **Frontend**: `monitoring-agent-app` service
- **Backend**: Internal service (access via port-forward)
- **Prometheus**: Monitoring and metrics collection
- **Grafana**: Dashboards and visualization

**Tunnels Created**:
- **Frontend Tunnel**: `http://127.0.0.1:XXXXX` (dynamic port)
- **Prometheus Tunnel**: `http://127.0.0.1:XXXXX` (dynamic port)
- **Grafana Tunnel**: `http://127.0.0.1:XXXXX` (dynamic port)

### verify.sh - Comprehensive Testing Solution

**Features**:
- ✅ **Tunnel Detection**: Automatically finds tunnel URLs from deploy.sh
- ✅ **Localhost Testing**: Tests only localhost connections (no minikube IP)
- ✅ **Early Exit**: Stops testing on first failure
- ✅ **Service Validation**: Tests all services and metrics endpoints
- ✅ **Status Reporting**: Clear success/failure feedback
- ✅ **URL Display**: Shows all accessible URLs

**Tests Performed**:
- **Frontend Service**: Main application endpoint
- **Frontend Metrics**: Prometheus metrics endpoint
- **Prometheus Service**: Monitoring interface
- **Grafana Service**: Dashboard interface

### cleanup.sh - Complete Cleanup Solution

**Features**:
- ✅ **Tunnel Cleanup**: Stops all minikube service tunnels
- ✅ **File Cleanup**: Removes tunnel URL and PID files
- ✅ **Service Deletion**: Deletes all Kubernetes services and deployments
- ✅ **Resource Cleanup**: Removes configuration resources (configmaps)
- ✅ **Status Verification**: Checks for remaining resources
- ✅ **Confirmation Prompt**: Asks for confirmation before cleanup (optional --force)

**Resources Cleaned Up**:
- **Services**: frontend-service, backend-service, prometheus-service, grafana-service
- **Deployments**: frontend-deployment, backend-deployment, prometheus-deployment, grafana-deployment
- **ConfigMaps**: prometheus-configmap, grafana-configmap, grafana-dashboard-configmap
- **Tunnels**: All minikube service tunnel processes
- **Files**: All tunnel URL and PID files in /tmp/

## 🔧 How It Works

### Tunnel Management System

1. **Cleanup**: Removes any existing tunnels
2. **Creation**: Starts new tunnels for all services
3. **URL Capture**: Captures tunnel URLs and stores them
4. **Verification**: Tests tunnel connectivity

### URL Storage System

Tunnel URLs are stored in temporary files:
```
/tmp/monitoring-agent-app_tunnel_url_final.txt
/tmp/prometheus-service_tunnel_url_final.txt
/tmp/grafana-service_tunnel_url_final.txt
```

### Service Testing Flow

1. **Detect Tunnels**: Read tunnel URLs from storage files
2. **Test Services**: Test each service via localhost tunnel
3. **Early Exit**: Stop on first failure
4. **Report Status**: Display comprehensive results

## 📊 Example Output

### deploy.sh Output
```bash
=== Starting Service Tunnels ===
Starting tunnel for Frontend...
  ✅ Frontend tunnel started: http://127.0.0.1:58711
Starting tunnel for Prometheus...
  ✅ Prometheus tunnel started: http://127.0.0.1:30090
Starting tunnel for Grafana...
  ✅ Grafana tunnel started: http://127.0.0.1:30091

=== Localhost Access URLs ===
All services are now accessible via localhost tunnels:
  Frontend:      http://127.0.0.1:58711
  Frontend Metrics: http://127.0.0.1:58711/metrics
  Prometheus:    http://127.0.0.1:30090
  Grafana:       http://127.0.0.1:30091 (admin/admin)

✅ Deployment and tunnel setup complete!
```

### verify.sh Output
```bash
=== Verifying Application Deployment ===
Detecting tunnel URLs from deployment...
✅ Found frontend tunnel: http://127.0.0.1:58711
✅ Found Prometheus tunnel: http://127.0.0.1:30090
✅ Found Grafana tunnel: http://127.0.0.1:30091

Testing Frontend service at http://127.0.0.1:58711
✅ Frontend service accessible via localhost tunnel

Testing frontend metrics...
✅ Frontend metrics accessible via localhost tunnel

=== Verifying Monitoring Stack ===
Testing Prometheus service at http://127.0.0.1:30090
✅ Prometheus service accessible via localhost tunnel

Testing Grafana service at http://127.0.0.1:30091
✅ Grafana service accessible via localhost tunnel

✅ All services verified successfully via localhost tunnels!
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Tunnels Not Starting
**Symptoms**: No tunnel URLs detected
**Solution**: 
```bash
# Check if minikube is running
minikube status

# Restart minikube if needed
minikube stop && minikube start

# Run deploy.sh again
./deploy.sh
```

#### 2. Services Not Accessible
**Symptoms**: curl failures on localhost URLs
**Solution**:
```bash
# Check tunnel processes
ps aux | grep "minikube service"

# Kill all tunnels and restart
pkill -f "minikube service"
./deploy.sh
```

#### 3. Port Conflicts
**Symptoms**: Tunnel creation fails
**Solution**:
```bash
# Clean up all tunnels and services
./cleanup.sh --force
./deploy.sh
```

#### 4. Complete Reset Needed
**Symptoms**: Multiple issues, services in inconsistent state
**Solution**:
```bash
# Complete cleanup and redeploy
./cleanup.sh --force
./deploy.sh
./verify.sh
```

### Manual Tunnel Management

If needed, you can manage tunnels manually:

```bash
# Start individual tunnels
minikube service monitoring-agent-app --url
minikube service prometheus-service --url
minikube service grafana-service --url

# Stop all tunnels
pkill -f "minikube service"

# Check tunnel status
ps aux | grep "minikube service"
```

## 🔄 Workflow Integration

### Development Workflow

1. **Make Changes**: Modify application code
2. **Deploy**: Run `./deploy.sh`
3. **Test**: Run `./verify.sh`
4. **Clean Up** (optional): Run `./cleanup.sh` when done
5. **Iterate**: Repeat as needed

### Complete Workflow Examples

**Full Development Cycle**:
```bash
# Deploy everything
./deploy.sh

# Test everything
./verify.sh

# Work on your application...

# Clean up when done
./cleanup.sh
```

**Quick Redeploy**:
```bash
# Clean up and redeploy
./cleanup.sh --force && ./deploy.sh && ./verify.sh
```

### CI/CD Integration

```bash
# In your CI/CD pipeline:
./deploy.sh && ./verify.sh
# Exit code will be non-zero if verification fails
```

### Automated Testing

```bash
#!/bin/bash
# Automated test script
set -e

echo "Deploying services..."
./deploy.sh

echo "Verifying services..."
./verify.sh

echo "All tests passed!"
```

## 📈 Benefits

### Before Enhancement
- ❌ Manual tunnel management required
- ❌ Services not accessible via minikube IP
- ❌ Dynamic port assignment issues
- ❌ Complex manual testing process
- ❌ Multiple terminal windows needed

### After Enhancement
- ✅ **Single Command Deployment**: `./deploy.sh` does everything
- ✅ **Single Command Testing**: `./verify.sh` verifies all services
- ✅ **Automatic Tunnel Management**: No manual intervention needed
- ✅ **Reliable Localhost Access**: All services accessible via localhost
- ✅ **Early Exit on Failure**: Fast feedback on issues
- ✅ **Comprehensive Testing**: All services and metrics tested

## 🎯 Best Practices

1. **Always run deploy.sh first**: Ensures fresh tunnels and deployment
2. **Use verify.sh after deployment**: Validates everything is working
3. **Check exit codes**: Scripts exit with non-zero on failure
4. **Clean up on exit**: Scripts handle cleanup automatically
5. **Monitor tunnel status**: Use `ps aux | grep "minikube service"` if needed

## 🔗 Related Documentation

- [Minikube Access Issues and Solutions](../docs/minikube-access-issues-and-solutions.md) - Comprehensive documentation of all issues and solutions
- [ETL Pipeline Configuration Usage](../docs/etl_configuration_usage.md) - ETL configuration documentation
- [ETL MVP Plan](../docs/etl_mvp_plan.md) - ETL implementation plan

## 🚀 Getting Started

1. **Ensure Minikube is running**:
   ```bash
   minikube status
   ```

2. **Deploy everything**:
   ```bash
   ./deploy.sh
   ```

3. **Verify everything works**:
   ```bash
   ./verify.sh
   ```

4. **Access your services**:
   - Use the URLs displayed by the scripts
   - All services are accessible via localhost
   - No need to remember minikube IP or NodePorts

5. **Clean up when done** (optional):
   ```bash
   ./cleanup.sh
   ```

## 🧹 Cleanup Script Options

### Usage Options

```bash
# Interactive cleanup (asks for confirmation)
./cleanup.sh

# Force cleanup (no confirmation prompt)
./cleanup.sh --force

# Show help
./cleanup.sh --help
```

### What Gets Cleaned Up

**Services**:
- frontend-service
- backend-service  
- prometheus-service
- grafana-service

**Deployments**:
- frontend-deployment
- backend-deployment
- prometheus-deployment
- grafana-deployment

**ConfigMaps**:
- prometheus-configmap
- grafana-configmap
- grafana-dashboard-configmap

**Tunnels**:
- All minikube service tunnel processes
- All tunnel URL and PID files in /tmp/

### Example Cleanup Output

```bash
=== Cleaning Up Deployment ===
Stopping minikube service tunnels...
Found active minikube service tunnels, stopping them...
✅ All minikube service tunnels stopped
✅ Tunnel URL files cleaned up

Stopping Kubernetes services...
Stopping monitoring stack...
service "grafana-service" deleted
deployment.apps "grafana-deployment" deleted
service "prometheus-service" deleted
deployment.apps "prometheus-deployment" deleted

Stopping application services...
service "frontend-service" deleted
deployment.apps "frontend-deployment" deleted
service "backend-service" deleted
deployment.apps "backend-deployment" deleted

✅ All Kubernetes services stopped
✅ No application pods remaining
✅ No application services remaining

=== Cleanup Summary ===
✅ Stopped all minikube service tunnels
✅ Removed tunnel URL files
✅ Deleted Kubernetes services and deployments
✅ Deleted configuration resources

✅ Cleanup complete!
```

That's it! Your complete monitoring stack is now deployed and accessible via reliable localhost tunnels. 🎉
