# Test through ingress with Host header
INGRESS_HOST=$(minikube ip)
echo "Hitting ingress at $INGRESS_HOST with Host header monitoring-agent-app.local"
curl -v -H "Host: monitoring-agent-app.local" http://$INGRESS_HOST/ || echo "Ingress test failed, trying alternative methods..."

# Alternative: Test via NodePort
NODEPORT=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.spec.ports[?(@.port==80)].nodePort}')
echo "Testing via NodePort $NODEPORT..."
curl -v -H "Host: monitoring-agent-app.local" http://$INGRESS_HOST:$NODEPORT/ || echo "NodePort test also failed"

# Alternative: Test via localhost (if /etc/hosts is updated)
echo "Testing via localhost (requires /etc/hosts update)..."
curl -v http://monitoring-agent-app.local/ || echo "Localhost test failed - /etc/hosts may not be updated"

# Check ingress status
kubectl get ingress
kubectl describe ingress monitoring-agent-app-ingress

# Check backend services are ClusterIP only
kubectl get services