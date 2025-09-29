#!/bin/bash

# Function to detect tunnel URLs from deploy.sh output
detect_tunnel_urls() {
    echo "Detecting tunnel URLs from deployment..."
    
    # Check for tunnel URL files created by deploy.sh
    if [ -f "/tmp/monitoring-agent-app_tunnel_url_final.txt" ]; then
        FRONTEND_TUNNEL_URL=$(cat "/tmp/monitoring-agent-app_tunnel_url_final.txt")
        echo "✅ Found frontend tunnel: $FRONTEND_TUNNEL_URL"
    else
        echo "❌ No frontend tunnel URL found. Run deploy.sh first."
        return 1
    fi
    
    if [ -f "/tmp/prometheus-service_tunnel_url_final.txt" ]; then
        PROMETHEUS_TUNNEL_URL=$(cat "/tmp/prometheus-service_tunnel_url_final.txt")
        echo "✅ Found Prometheus tunnel: $PROMETHEUS_TUNNEL_URL"
    else
        echo "❌ No Prometheus tunnel URL found. Run deploy.sh first."
        return 1
    fi
    
    if [ -f "/tmp/grafana-service_tunnel_url_final.txt" ]; then
        GRAFANA_TUNNEL_URL=$(cat "/tmp/grafana-service_tunnel_url_final.txt")
        echo "✅ Found Grafana tunnel: $GRAFANA_TUNNEL_URL"
    else
        echo "❌ No Grafana tunnel URL found. Run deploy.sh first."
        return 1
    fi
    
    return 0
}

# Function to test a service via localhost tunnel
test_service() {
    local service_name=$1
    local localhost_url=$2
    local test_description=$3
    
    echo "Testing $test_description at $localhost_url"
    if curl -s --max-time 10 "$localhost_url" > /dev/null 2>&1; then
        echo "✅ $test_description accessible via localhost tunnel"
        return 0
    else
        echo "❌ $test_description failed via localhost tunnel"
        return 1
    fi
}

# Function to exit script on failure
exit_on_failure() {
    local exit_code=$1
    local test_name=$2
    if [ $exit_code -ne 0 ]; then
        echo ""
        echo "❌ $test_name failed. Stopping verification process."
        echo "Please check the service status and try again."
        exit $exit_code
    fi
}

echo "=== Verifying Application Deployment ==="

# Detect tunnel URLs from deploy.sh
detect_tunnel_urls
exit_on_failure $? "Tunnel detection"

# Test frontend service
test_service "frontend" "$FRONTEND_TUNNEL_URL" "Frontend service"
exit_on_failure $? "Frontend service"

# Test frontend metrics
echo "Testing frontend metrics..."
test_service "frontend-metrics" "${FRONTEND_TUNNEL_URL}/metrics" "Frontend metrics"
exit_on_failure $? "Frontend metrics"

echo ""
echo "=== Verifying Monitoring Stack ==="

# Test Prometheus
test_service "prometheus" "$PROMETHEUS_TUNNEL_URL" "Prometheus service"
exit_on_failure $? "Prometheus service"

# Test Grafana
test_service "grafana" "$GRAFANA_TUNNEL_URL" "Grafana service"
exit_on_failure $? "Grafana service"

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
echo "=== Localhost Access URLs ==="
echo "All services are accessible via localhost tunnels:"
echo "  Frontend:      $FRONTEND_TUNNEL_URL"
echo "  Frontend Metrics: ${FRONTEND_TUNNEL_URL}/metrics"
echo "  Prometheus:    $PROMETHEUS_TUNNEL_URL"
echo "  Grafana:       $GRAFANA_TUNNEL_URL (admin/admin)"
echo ""
echo "Backend Access (requires separate port-forward):"
echo "  kubectl port-forward service/backend-service 8081:5000"
echo "  Then: http://localhost:8081/api/data"
echo ""
echo "💡 Tunnel Management:"
echo "  Stop all tunnels: pkill -f 'minikube service'"
echo "  List tunnels: ps aux | grep 'minikube service'"
echo "  Restart tunnels: Run ./deploy.sh again"
echo ""
echo "✅ All services verified successfully via localhost tunnels!"
echo ""
echo "=== Verification Complete ==="
echo "All tests passed successfully!"