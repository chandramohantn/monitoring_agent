# Test frontend via NodePort
MINIKUBE_IP=$(minikube ip)
NODEPORT=$(kubectl get service monitoring-agent-app -o jsonpath='{.spec.ports[0].nodePort}')
echo "Testing frontend at $MINIKUBE_IP:$NODEPORT"
curl -v http://$MINIKUBE_IP:$NODEPORT/ || echo "Frontend test failed"

# Test frontend metrics
echo "Testing frontend metrics..."
curl -v http://$MINIKUBE_IP:$NODEPORT/metrics || echo "Frontend metrics test failed"

# Check service status
kubectl get services
kubectl describe service monitoring-agent-app

# Check pods status
kubectl get pods