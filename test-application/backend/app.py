from flask import Flask, jsonify, request
import time
import random
import psutil
import os
from prometheus_client import Counter, Histogram, Gauge, generate_latest

app = Flask(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('backend_request_total', 'Total requests to backend')
ERROR_COUNT = Counter('backend_error_total', 'Total errors in backend')
REQUEST_LATENCY = Histogram('backend_request_latency_seconds', 'Backend request latency')
CPU_USAGE = Gauge('backend_cpu_usage_percent', 'Backend CPU usage')
MEMORY_USAGE = Gauge('backend_memory_usage_mb', 'Backend memory usage')
THROUGHPUT = Gauge('backend_throughput_rps', 'Backend throughput')

REQUEST_TIMESTAMPS = []  # Track timestamps of recent requests
THROUGHPUT_WINDOW = 10  # Calculate RPS over last 10 seconds

def update_throughput():
    """Calculate requests per second over a sliding window"""
    current_time = time.time()
    # Remove timestamps older than our window
    global REQUEST_TIMESTAMPS
    REQUEST_TIMESTAMPS = [ts for ts in REQUEST_TIMESTAMPS if current_time - ts <= THROUGHPUT_WINDOW]
    
    # Calculate RPS
    rps = len(REQUEST_TIMESTAMPS) / THROUGHPUT_WINDOW
    THROUGHPUT.set(rps)

@app.route('/api/data')
def get_data():
    start_time = time.time()
    
    # Simulate some processing time
    processing_time = random.uniform(0.1, 0.5)
    time.sleep(processing_time)
    
    # Simulate occasional errors (5% error rate)
    if random.random() < 0.05:
        ERROR_COUNT.inc()
        return jsonify({"error": "Internal server error"}), 500
    
    REQUEST_COUNT.inc()
    REQUEST_LATENCY.observe(time.time() - start_time)

    # Add current timestamp for throughput calculation
    REQUEST_TIMESTAMPS.append(time.time())
    update_throughput()
    
    return jsonify({
        "data": f"Processed in {processing_time:.2f}s",
        "timestamp": time.time()
    })

@app.route('/api/health')
def health_check():
    # Update resource metrics
    CPU_USAGE.set(psutil.cpu_percent())
    MEMORY_USAGE.set(psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024)  # MB
    
    return jsonify({"status": "healthy"})

@app.route('/metrics')
def metrics():
    return generate_latest()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)