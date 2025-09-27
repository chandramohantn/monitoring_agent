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
echo "Deploying application services..."
kubectl apply -f kubernetes/deployments/backend-deployment.yaml
kubectl apply -f kubernetes/services/backend-service.yaml
kubectl apply -f kubernetes/deployments/frontend-deployment.yaml
kubectl apply -f kubernetes/services/frontend-service.yaml

# Deploy monitoring stack
echo "Deploying monitoring stack..."
kubectl apply -f kubernetes/configmaps/prometheus-configmap.yaml
kubectl apply -f kubernetes/deployments/prometheus-deployment.yaml
kubectl apply -f kubernetes/services/prometheus-service.yaml
kubectl apply -f kubernetes/configmaps/grafana-configmap.yaml
kubectl apply -f kubernetes/configmaps/grafana-dashboard-configmap.yaml
kubectl apply -f kubernetes/deployments/grafana-deployment.yaml
kubectl apply -f kubernetes/services/grafana-service.yaml

# Wait for pods to be ready
echo "Waiting for application pods to be ready..."
kubectl wait --for=condition=ready pod -l app=monitoring-agent-app --timeout=120s
kubectl wait --for=condition=ready pod -l app=backend --timeout=120s

echo "Waiting for monitoring pods to be ready..."
kubectl wait --for=condition=ready pod -l app=prometheus --timeout=120s
kubectl wait --for=condition=ready pod -l app=grafana --timeout=120s

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Get minikube IP and NodePorts
MINIKUBE_IP=$(minikube ip)
FRONTEND_NODEPORT=$(kubectl get service monitoring-agent-app -o jsonpath='{.spec.ports[0].nodePort}')
PROMETHEUS_NODEPORT=$(kubectl get service prometheus-service -o jsonpath='{.spec.ports[0].nodePort}')
GRAFANA_NODEPORT=$(kubectl get service grafana-service -o jsonpath='{.spec.ports[0].nodePort}')

echo "Minikube IP: $MINIKUBE_IP"
echo "Frontend NodePort: $FRONTEND_NODEPORT"
echo "Prometheus NodePort: $PROMETHEUS_NODEPORT"
echo "Grafana NodePort: $GRAFANA_NODEPORT"

echo ""
echo "Application URLs:"
echo "  Frontend:      http://$MINIKUBE_IP:$FRONTEND_NODEPORT/"
echo "  Frontend Metrics: http://$MINIKUBE_IP:$FRONTEND_NODEPORT/metrics"
echo ""
echo "Monitoring URLs:"
echo "  Prometheus:    http://$MINIKUBE_IP:$PROMETHEUS_NODEPORT/"
echo "  Grafana:       http://$MINIKUBE_IP:$GRAFANA_NODEPORT/ (admin/admin)"
echo ""
echo "Backend is internal only. To access backend:"
echo "  kubectl port-forward service/backend-service 8081:5000"
echo "  Then: http://localhost:8081/api/data"
echo ""
echo "Deployment complete!"