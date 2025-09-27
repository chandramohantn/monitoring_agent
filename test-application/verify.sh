#!/bin/bash

echo "=== Verifying Application Deployment ==="

# Test frontend via NodePort
MINIKUBE_IP=$(minikube ip)
FRONTEND_NODEPORT=$(kubectl get service monitoring-agent-app -o jsonpath='{.spec.ports[0].nodePort}')
echo "Testing frontend at $MINIKUBE_IP:$FRONTEND_NODEPORT"
curl -v http://$MINIKUBE_IP:$FRONTEND_NODEPORT/ || echo "Frontend test failed"

# Test frontend metrics
echo "Testing frontend metrics..."
curl -v http://$MINIKUBE_IP:$FRONTEND_NODEPORT/metrics || echo "Frontend metrics test failed"

echo ""
echo "=== Verifying Monitoring Stack ==="

# Test Prometheus
PROMETHEUS_NODEPORT=$(kubectl get service prometheus-service -o jsonpath='{.spec.ports[0].nodePort}')
echo "Testing Prometheus at $MINIKUBE_IP:$PROMETHEUS_NODEPORT"
curl -v http://$MINIKUBE_IP:$PROMETHEUS_NODEPORT/ || echo "Prometheus test failed"

# Test Grafana
GRAFANA_NODEPORT=$(kubectl get service grafana-service -o jsonpath='{.spec.ports[0].nodePort}')
echo "Testing Grafana at $MINIKUBE_IP:$GRAFANA_NODEPORT"
curl -v http://$MINIKUBE_IP:$GRAFANA_NODEPORT/ || echo "Grafana test failed"

echo ""
echo "=== Checking Service Status ==="
kubectl get services

echo ""
echo "=== Checking Pod Status ==="
kubectl get pods

echo ""
echo "=== Checking Prometheus Targets ==="
echo "Prometheus should be scraping the following targets:"
echo "- Frontend service (port 8000)"
echo "- Backend service (port 5000)"
echo "- Prometheus itself (port 9090)"

echo ""
echo "=== Access URLs ==="
echo "Frontend:      http://$MINIKUBE_IP:$FRONTEND_NODEPORT/"
echo "Prometheus:    http://$MINIKUBE_IP:$PROMETHEUS_NODEPORT/"
echo "Grafana:       http://$MINIKUBE_IP:$GRAFANA_NODEPORT/ (admin/admin)"
echo ""
echo "To access backend:"
echo "kubectl port-forward service/backend-service 8081:5000"
echo "Then: http://localhost:8081/api/data"