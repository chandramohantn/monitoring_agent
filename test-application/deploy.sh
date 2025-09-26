#!/bin/bash

set -e  # Exit on error

echo "Building and deploying test application with NodePort..."

# Build Docker images
echo "Building Docker images..."
docker build -t backend:latest backend/
docker build -t frontend:latest frontend/

# Load images into minikube
echo "Loading images into minikube..."
minikube image load backend:latest
minikube image load frontend:latest

# Deploy to Kubernetes (excluding ingress)
echo "Deploying to Kubernetes..."
kubectl apply -f kubernetes/backend-deployment.yaml
kubectl apply -f kubernetes/backend-service.yaml
kubectl apply -f kubernetes/frontend-deployment.yaml
kubectl apply -f kubernetes/frontend-service.yaml

# Wait for pods to be ready
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=monitoring-agent-app --timeout=120s
kubectl wait --for=condition=ready pod -l app=backend --timeout=120s

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Get minikube IP and NodePort
MINIKUBE_IP=$(minikube ip)
NODEPORT=$(kubectl get service monitoring-agent-app -o jsonpath='{.spec.ports[0].nodePort}')
echo "Minikube IP: $MINIKUBE_IP"
echo "Frontend NodePort: $NODEPORT"

echo ""
echo "Application URLs:"
echo "  Frontend:      http://$MINIKUBE_IP:$NODEPORT/"
echo "  Frontend Metrics: http://$MINIKUBE_IP:$NODEPORT/metrics"
echo ""
echo "Backend is internal only. To access backend:"
echo "  kubectl port-forward service/backend-service 8081:5000"
echo "  Then: http://localhost:8081/api/data"
echo ""
echo "Deployment complete!"