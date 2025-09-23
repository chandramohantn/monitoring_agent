#!/bin/bash

# Kill any existing port-forward processes
pkill -f "kubectl port-forward" || true

echo "Starting port-forwarding for monitoring services..."

# Port-forward functions
start_port_forward() {
    local service_name=$1
    local local_port=$2
    local remote_port=$3
    local namespace=$4
    
    echo "Forwarding $service_name: localhost:$local_port -> $remote_port"
    kubectl port-forward -n "$namespace" "svc/$service_name" "$local_port:$remote_port" &
}

# Start port-forwarding for monitoring services
start_port_forward "prometheus-kube-prometheus-prometheus" 9090 9090 "monitoring"
start_port_forward "prometheus-grafana" 8081 80 "monitoring"

echo ""
echo "Monitoring services available at:"
echo "  Prometheus:    http://localhost:9090"
echo "  Grafana:       http://localhost:8081 (admin/prom-operator)"
echo ""
echo "Application is available via Ingress: http://$(minikube ip)"
echo ""
echo "Press Ctrl+C to stop all port-forwarding"

# Wait for Ctrl+C
trap 'echo ""; echo "Stopping port-forwarding..."; pkill -f "kubectl port-forward"; exit 0' INT
wait