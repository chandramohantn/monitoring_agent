#!/bin/bash

set -e  # Exit on error

echo "=== Cleaning Up Deployment ==="
echo "This will stop all services and tunnels started by deploy.sh"
echo ""

# Function to stop service tunnels
stop_service_tunnels() {
    echo "Stopping minikube service tunnels..."
    
    # Kill all minikube service processes
    if pgrep -f "minikube service" > /dev/null; then
        echo "Found active minikube service tunnels, stopping them..."
        pkill -f "minikube service"
        sleep 3
        
        # Verify tunnels are stopped
        if pgrep -f "minikube service" > /dev/null; then
            echo "⚠️  Some tunnels may still be running, force killing..."
            pkill -9 -f "minikube service"
            sleep 2
        fi
        
        echo "✅ All minikube service tunnels stopped"
    else
        echo "✅ No active minikube service tunnels found"
    fi
    
    # Clean up tunnel URL files
    echo "Cleaning up tunnel URL files..."
    rm -f /tmp/*_tunnel_url.txt
    rm -f /tmp/*_tunnel_url_final.txt
    rm -f /tmp/*_tunnel_pid.txt
    echo "✅ Tunnel URL files cleaned up"
}

# Function to stop Kubernetes services
stop_kubernetes_services() {
    echo ""
    echo "Stopping Kubernetes services..."
    
    # Stop monitoring stack services
    echo "Stopping monitoring stack..."
    kubectl delete service grafana-service 2>/dev/null || echo "  Grafana service not found"
    kubectl delete deployment grafana-deployment 2>/dev/null || echo "  Grafana deployment not found"
    kubectl delete service prometheus-service 2>/dev/null || echo "  Prometheus service not found"
    kubectl delete deployment prometheus-deployment 2>/dev/null || echo "  Prometheus deployment not found"
    
    # Stop application services
    echo "Stopping application services..."
    kubectl delete service frontend-service 2>/dev/null || echo "  Frontend service not found"
    kubectl delete deployment frontend-deployment 2>/dev/null || echo "  Frontend deployment not found"
    kubectl delete service backend-service 2>/dev/null || echo "  Backend service not found"
    kubectl delete deployment backend-deployment 2>/dev/null || echo "  Backend deployment not found"
    
    # Stop configmaps
    echo "Stopping configuration resources..."
    kubectl delete configmap grafana-dashboard-configmap 2>/dev/null || echo "  Grafana dashboard configmap not found"
    kubectl delete configmap grafana-configmap 2>/dev/null || echo "  Grafana configmap not found"
    kubectl delete configmap prometheus-configmap 2>/dev/null || echo "  Prometheus configmap not found"
    
    echo "✅ All Kubernetes services stopped"
}

# Function to check if services are still running
check_remaining_services() {
    echo ""
    echo "Checking for remaining services..."
    
    # Check for remaining pods
    local remaining_pods=$(kubectl get pods -l "app in (monitoring-agent-app,backend,prometheus,grafana)" --no-headers 2>/dev/null | wc -l)
    if [ "$remaining_pods" -gt 0 ]; then
        echo "⚠️  $remaining_pods pods still running:"
        kubectl get pods -l "app in (monitoring-agent-app,backend,prometheus,grafana)" 2>/dev/null || true
    else
        echo "✅ No application pods remaining"
    fi
    
    # Check for remaining services
    local remaining_services=$(kubectl get services -l "app in (monitoring-agent-app,backend,prometheus,grafana)" --no-headers 2>/dev/null | wc -l)
    if [ "$remaining_services" -gt 0 ]; then
        echo "⚠️  $remaining_services services still running:"
        kubectl get services -l "app in (monitoring-agent-app,backend,prometheus,grafana)" 2>/dev/null || true
    else
        echo "✅ No application services remaining"
    fi
}

# Function to display cleanup summary
display_cleanup_summary() {
    echo ""
    echo "=== Cleanup Summary ==="
    echo "✅ Stopped all minikube service tunnels"
    echo "✅ Removed tunnel URL files"
    echo "✅ Deleted Kubernetes services and deployments"
    echo "✅ Deleted configuration resources"
    echo ""
    echo "=== Remaining Resources ==="
    
    # Check for any remaining resources
    local remaining_pods=$(kubectl get pods --no-headers 2>/dev/null | wc -l)
    local remaining_services=$(kubectl get services --no-headers 2>/dev/null | wc -l)
    
    if [ "$remaining_pods" -gt 0 ] || [ "$remaining_services" -gt 0 ]; then
        echo "Other resources still present in cluster:"
        echo "  Pods: $remaining_pods"
        echo "  Services: $remaining_services"
        echo ""
        echo "To see all remaining resources:"
        echo "  kubectl get all"
    else
        echo "✅ No resources remaining in cluster"
    fi
    
    echo ""
    echo "=== Next Steps ==="
    echo "• To redeploy: ./deploy.sh"
    echo "• To verify deployment: ./verify.sh"
    echo "• To check cluster status: kubectl get all"
    echo ""
    echo "✅ Cleanup complete!"
}

# Main cleanup process
main() {
    # Confirm cleanup action
    echo "This will perform the following actions:"
    echo "1. Stop all minikube service tunnels"
    echo "2. Remove tunnel URL files"
    echo "3. Delete all deployed Kubernetes services and deployments"
    echo "4. Delete configuration resources"
    echo ""
    
    # Ask for confirmation (optional - can be skipped with --force flag)
    if [ "$1" != "--force" ]; then
        read -p "Do you want to continue? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Cleanup cancelled."
            exit 0
        fi
    fi
    
    # Perform cleanup steps
    stop_service_tunnels
    stop_kubernetes_services
    check_remaining_services
    display_cleanup_summary
}

# Handle command line arguments
case "${1:-}" in
    "--help" | "-h")
        echo "Usage: $0 [--force]"
        echo ""
        echo "Options:"
        echo "  --force    Skip confirmation prompt"
        echo "  --help     Show this help message"
        echo ""
        echo "This script stops all services and tunnels started by deploy.sh"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
