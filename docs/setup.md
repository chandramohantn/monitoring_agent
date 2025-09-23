# Test Application & Monitoring Infrastructure Setup Guide

## Overview
This guide will help you create and deploy a dummy Python application with frontend/backend services, instrument them for metrics, and set up monitoring infrastructure.

## Prerequisites

 - Completed the prerequisites setup from the previous guide
 - Minikube cluster running with monitoring stack installed
 - kubectl and helm configured

## Create Test Application Structure

### Create the application directory structure
```
mkdir -p test-application/{frontend,backend,kubernetes,load-generator,grafana-dashboards}
cd test-application
```

### Project structure should look like:
```
test-application/
├── frontend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── kubernetes/
│   ├── frontend-deployment.yaml
│   ├── backend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── backend-service.yaml
│   └── ingress.yaml
├── load-generator/
│   └── load_test.py
└── grafana-dashboards/
    └── application-metrics.json
```

## Create the Backend Service

 - Create backend/app.py
 - Create backend/requirements.txt
 - Create backend/Dockerfile

## Create the Frontend Service

 - Create frontend/app.py
 - Create frontend/requirements.txt
 - Create frontend/Dockerfile

## Create Kubernetes Manifests

 - Create kubernetes/backend-deployment.yaml
 - Create kubernetes/frontend-deployment.yaml
 - Create kubernetes/backend-service.yaml
 - Create kubernetes/frontend-service.yaml
 - Create kubernetes/ingress.yaml

## Create Load Generator

 - Create load-generator/load_test.py
 - Create load-generator/requirements.txt

## Build and Deploy Application

 - Build Docker images
 - Deploy to Kubernetes
 - Access the application

## Start Load Testing

 - Start the load generator
 - Alternatively, deploy load generator as a Kubernetes job

## Create Grafana Dashboard

 - Create grafana-dashboards/application-metrics.json
 - Import dashboard to Grafana

## Verification

 - Verify application is working
 - Verify Prometheus scraping
 - Verify metrics in Grafana

## Troubleshooting

### Common issues:
 - Images not found: Ensure images are loaded into minikube with minikube image load
 - Services not accessible: Check service types and ports with kubectl get svc
 - Metrics not scraping: Verify Prometheus annotations in deployment YAMLs
 - Application errors: Check logs with kubectl logs <pod-name>

### Debug commands:
#### Check pod status
 - kubectl get pods

#### View pod logs
 - kubectl logs -l app=frontend

#### Check service endpoints
 - kubectl get endpoints

#### Verify Prometheus service discovery
 - kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus
