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

# Function to start service tunnels
start_service_tunnel() {
    local service_name=$1
    local service_display_name=$2
    
    echo "Starting tunnel for $service_display_name..."
    # Start tunnel in background and capture the process
    minikube service "$service_name" --url > "/tmp/${service_name}_tunnel_url.txt" 2>&1 &
    local tunnel_pid=$!
    echo "$tunnel_pid" > "/tmp/${service_name}_tunnel_pid.txt"
    
    # Wait a moment for tunnel to establish
    sleep 3
    
    # Extract the URL from the tunnel output
    if [ -f "/tmp/${service_name}_tunnel_url.txt" ]; then
        local tunnel_url=$(cat "/tmp/${service_name}_tunnel_url.txt" | grep -o "http://[^[:space:]]*" | head -1)
        if [ -n "$tunnel_url" ]; then
            echo "  ✅ $service_display_name tunnel started: $tunnel_url"
            echo "$tunnel_url" > "/tmp/${service_name}_tunnel_url_final.txt"
        else
            echo "  ⚠️  $service_display_name tunnel started but URL not detected"
        fi
    fi
}

# Start tunnels for all services
echo "=== Starting Service Tunnels ==="
echo "This will create localhost tunnels for all services..."

# Kill any existing tunnels first
echo "Cleaning up existing tunnels..."
pkill -f "minikube service" 2>/dev/null || true
sleep 2

# Start tunnels for each service
start_service_tunnel "monitoring-agent-app" "Frontend"
start_service_tunnel "prometheus-service" "Prometheus" 
start_service_tunnel "grafana-service" "Grafana"

echo ""
echo "=== Tunnel Status ==="
echo "Active tunnels:"
ps aux | grep "minikube service" | grep -v grep | while read line; do
    echo "  - $line"
done

echo ""
echo "=== Localhost Access URLs ==="
echo "All services are now accessible via localhost tunnels:"

# Display tunnel URLs
if [ -f "/tmp/monitoring-agent-app_tunnel_url_final.txt" ]; then
    FRONTEND_TUNNEL=$(cat "/tmp/monitoring-agent-app_tunnel_url_final.txt")
    echo "  Frontend:      $FRONTEND_TUNNEL"
    echo "  Frontend Metrics: ${FRONTEND_TUNNEL}/metrics"
fi

if [ -f "/tmp/prometheus-service_tunnel_url_final.txt" ]; then
    PROMETHEUS_TUNNEL=$(cat "/tmp/prometheus-service_tunnel_url_final.txt")
    echo "  Prometheus:    $PROMETHEUS_TUNNEL"
fi

if [ -f "/tmp/grafana-service_tunnel_url_final.txt" ]; then
    GRAFANA_TUNNEL=$(cat "/tmp/grafana-service_tunnel_url_final.txt")
    echo "  Grafana:       $GRAFANA_TUNNEL (admin/admin)"
fi

echo ""
echo "💡 Tunnel Management:"
echo "  Stop all tunnels: pkill -f 'minikube service'"
echo "  List tunnels: ps aux | grep 'minikube service'"
echo ""
echo "✅ Deployment and tunnel setup complete!"
echo "Run './verify.sh' to test all services via localhost tunnels."