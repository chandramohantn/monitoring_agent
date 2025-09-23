# Prerequisites Setup Guide

## Python Environment Setup with uv
### On macOS/Linux
 - curl -LsSf https://astral.sh/uv/install.sh | sh

### Alternatively, via pip (if you have Python already)
 - pip install uv

### Create and Initialize Python Environment
 - uv python install 3.13
 - uv init --python 3.13

### Create pyproject.toml with Dependencies
 - Create a toml file with all dependencies

### Install Dependencies
uv sync


## Setup minikube, kubectl and helm
### Install minikube
### macOS
 - brew install minikube

### Linux
 - curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
 - sudo install minikube-linux-amd64 /usr/local/bin/minikube

### Install kubectl
### macOS
 - brew install kubectl

### Linux
 - curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
 - sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

### Install helm
### macOS
 - brew install helm

### Linux
 - curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

### Verify installations
 - minikube version
 - kubectl version --client
 - helm version

## Setup Minikube Cluster and Monitoring Stack
### Start minikube cluster
 - minikube start --cpus=4 --memory=8192 --disk-size=20g

### Enable required addons
 - minikube addons enable metrics-server
 - minikube addons enable dashboard

### Install Prometheus Stack using Helm
### Add prometheus-community helm repository
 - helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
 - helm repo update

### Install kube-prometheus stack
 - helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

### Verify installation
### Check all pods are running
 - kubectl get pods -n monitoring

### Access Prometheus (in a new terminal)
 - kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090

### Access Grafana (in a new terminal)
 - kubectl port-forward -n monitoring svc/prometheus-grafana 8080:80
### Grafana username: admin, password: prom-operator

### Install Chaos Mesh for fault injection
### Install Chaos Mesh
 - helm repo add chaos-mesh https://charts.chaos-mesh.org
 - helm install chaos-mesh chaos-mesh/chaos-mesh --namespace=chaos-mesh --create-namespace --set dashboard.create=true

### Verify installation
 - kubectl get pods -n chaos-mesh

### Access Chaos Dashboard (in a new terminal)
 - kubectl port-forward -n chaos-mesh svc/chaos-dashboard 2333:2333

## Setup Minikube Dashboard
### Access Kubernetes Dashboard
 - minikube dashboard

## Verify Complete Setup
### Run verification script
 - Create a verification script which will allow us to test all the components which have been installed earlier.
 - uv run verify_setup.py


## Common issues and solutions:
### Minikube won't start
 - minikube delete && minikube start --cpus=4 --memory=8192

### Helm charts fail to install
 - Check network connectivity to chart repositories
 - Verify Kubernetes cluster is running: kubectl cluster-info

### Python dependencies conflict
 - Use uv's resolution: uv sync --frozen
 - Check for version conflicts in pyproject.toml

### Port conflicts
 - Change port forwarding ports if defaults are occupied
