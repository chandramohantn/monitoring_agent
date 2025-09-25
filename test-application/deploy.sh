#!/bin/bash

set -e  # Exit on error

echo "Building and deploying test application with Ingress..."

# Enable ingress if not already enabled
if ! minikube addons list | grep -q "ingress.*enabled"; then
    echo "Enabling Ingress addon..."
    minikube addons enable ingress
fi

# Build Docker images
echo "Building Docker images..."
docker build -t backend:latest backend/
docker build -t frontend:latest frontend/

# Load images into minikube
echo "Loading images into minikube..."
minikube image load backend:latest
minikube image load frontend:latest

# Deploy to Kubernetes
echo "Deploying to Kubernetes..."
kubectl apply -f kubernetes/

# Wait for pods to be ready
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=monitoring-agent-app --timeout=120s
kubectl wait --for=condition=ready pod -l app=backend --timeout=120s

# Wait for ingress to be available
echo "Waiting for ingress controller..."
sleep 30  # Give ingress controller time to process the new ingress

# Start minikube tunnel for ingress access
echo "Starting minikube tunnel for ingress access..."
if ! pgrep -f "minikube tunnel" > /dev/null; then
    echo "Starting minikube tunnel in background..."
    minikube tunnel > /dev/null 2>&1 &
    TUNNEL_PID=$!
    echo "Minikube tunnel started with PID: $TUNNEL_PID"
    sleep 10  # Give tunnel time to establish
else
    echo "Minikube tunnel already running"
fi

# Get minikube IP and update /etc/hosts
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"

# # Update /etc/hosts (requires sudo)
# echo "Updating /etc/hosts to map monitoring-agent-app.local to $MINIKUBE_IP"
# if grep -q "monitoring-agent-app.local" /etc/hosts; then
#     sudo sed -i.bak "s/.*monitoring-agent-app.local/$MINIKUBE_IP monitoring-agent-app.local/" /etc/hosts
# else
#     echo "$MINIKUBE_IP monitoring-agent-app.local" | sudo tee -a /etc/hosts
# fi

echo ""
echo "Application URLs:"
echo "  Frontend:      http://monitoring-agent-app.local/"
echo "  Backend API:   http://monitoring-agent-app.local/api/data"
echo "  Frontend Metrics: http://monitoring-agent-app.local/metrics"
echo "  Backend Metrics:  http://monitoring-agent-app.local/backend-metrics"
echo ""
echo "Deployment complete!"