from flask import Flask, render_template, request
import requests
import time
import random
import psutil
import os
from prometheus_client import Counter, Histogram, Gauge, generate_latest

app = Flask(__name__)

# Prometheus metrics
FRONTEND_REQUEST_COUNT = Counter('frontend_request_total', 'Total requests to frontend')
FRONTEND_ERROR_COUNT = Counter('frontend_error_total', 'Total errors in frontend')
FRONTEND_LATENCY = Histogram('frontend_request_latency_seconds', 'Frontend request latency')
BACKEND_LATENCY = Histogram('frontend_backend_latency_seconds', 'Backend API call latency')
CPU_USAGE = Gauge('frontend_cpu_usage_percent', 'Frontend CPU usage')
MEMORY_USAGE = Gauge('frontend_memory_usage_mb', 'Frontend memory usage')

# Backend service URL (will be set via environment variable)
BACKEND_URL = os.getenv('BACKEND_URL', 'http://backend-service:5000')

@app.route('/')
def index():
    start_time = time.time()
    FRONTEND_REQUEST_COUNT.inc()
    
    try:
        # Call backend API
        backend_start = time.time()
        response = requests.get(f"{BACKEND_URL}/api/data", timeout=5)
        BACKEND_LATENCY.observe(time.time() - backend_start)
        
        if response.status_code == 200:
            data = response.json()
        else:
            data = {"error": "Backend unavailable"}
            FRONTEND_ERROR_COUNT.inc()
    except requests.exceptions.RequestException:
        data = {"error": "Backend connection failed"}
        FRONTEND_ERROR_COUNT.inc()
    
    FRONTEND_LATENCY.observe(time.time() - start_time)
    return f"""
    <html>
        <head><title>Test App</title></head>
        <body>
            <h1>Frontend Service</h1>
            <p>Backend Response: {data}</p>
            <p><a href="/metrics">Metrics</a></p>
        </body>
    </html>
    """

@app.route('/health')
def health():
    CPU_USAGE.set(psutil.cpu_percent())
    MEMORY_USAGE.set(psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024)
    return {"status": "healthy"}

@app.route('/metrics')
def metrics():
    return generate_latest()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)