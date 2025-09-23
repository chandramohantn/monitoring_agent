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
kubectl wait --for=condition=ready pod -l app=frontend --timeout=120s
kubectl wait --for=condition=ready pod -l app=backend --timeout=120s

# Wait for ingress to be available
echo "Waiting for ingress controller..."
sleep 30  # Give ingress controller time to process the new ingress

# Get minikube IP and update /etc/hosts
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"

# # Update /etc/hosts (requires sudo)
# if grep -q "test-app.local" /etc/hosts; then
#     sudo sed -i.bak "s/.*test-app.local/$MINIKUBE_IP test-app.local/" /etc/hosts
# else
#     echo "$MINIKUBE_IP test-app.local" | sudo tee -a /etc/hosts
# fi

echo ""
echo "Application URLs:"
echo "  Frontend:      http://test-app.local/"
echo "  Backend API:   http://test-app.local/api/data"
echo "  Frontend Metrics: http://test-app.local/metrics"
echo "  Backend Metrics:  http://test-app.local/backend-metrics"
echo ""
echo "Deployment complete!"