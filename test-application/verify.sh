# Test through ingress with Host header
curl -H "Host: test-app.local" http://$(minikube ip)/

# Or if you updated /etc/hosts
curl http://test-app.local/

# Check ingress status
kubectl get ingress
kubectl describe ingress test-app-ingress

# Check backend services are ClusterIP only
kubectl get services