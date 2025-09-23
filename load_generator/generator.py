import requests
import time
import random
import threading
import sys
from concurrent.futures import ThreadPoolExecutor
import subprocess

class LoadGenerator:
    def __init__(self, base_url, host_header="test-app.local", num_users=10):
        self.base_url = base_url
        self.host_header = host_header
        self.num_users = num_users
        self.running = False
        self.session = None
        
    def create_session(self):
        """Create a session with the host header"""
        session = requests.Session()
        session.headers.update({'Host': self.host_header})
        return session
        
    def user_behavior(self, user_id):
        """Simulate a user's behavior pattern"""
        session = self.create_session()
        request_count = 0
        
        while self.running:
            try:
                # Vary request patterns
                if random.random() < 0.7:  # 70% chance to hit frontend
                    start_time = time.time()
                    response = session.get(f"{self.base_url}/", timeout=10)
                    latency = time.time() - start_time
                    
                    if response.status_code == 200:
                        print(f"User {user_id}: Frontend OK (latency: {latency:.2f}s)")
                    else:
                        print(f"User {user_id}: Frontend ERROR {response.status_code}")
                
                # Occasionally call backend directly through ingress
                if random.random() < 0.3:  # 30% chance to call backend
                    session.get(f"{self.base_url}/api/data", timeout=5)
                    
                request_count += 1
                
                # Random delay between requests (0.5-5 seconds)
                time.sleep(random.uniform(0.5, 5))
                
            except requests.exceptions.RequestException as e:
                print(f"User {user_id}: Request failed - {e}")
                time.sleep(2)  # Back off on errors
    
    def start(self):
        """Start the load test"""
        self.running = True
        print(f"Starting load test with {self.num_users} users...")
        print(f"Target: {self.base_url} with Host: {self.host_header}")
        
        with ThreadPoolExecutor(max_workers=self.num_users) as executor:
            for user_id in range(self.num_users):
                executor.submit(self.user_behavior, user_id)
                
            # Keep running until interrupted
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()
    
    def stop(self):
        """Stop the load test"""
        self.running = False
        print("Stopping load test...")

def get_minikube_ip():
    try:
        result = subprocess.run(['minikube', 'ip'], capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "localhost"  # Fallback

if __name__ == "__main__":
    minikube_ip = get_minikube_ip()
    base_url = f"http://{minikube_ip}"  # Ingress controller IP
    
    generator = LoadGenerator(base_url, host_header="test-app.local", num_users=5)
    generator.start()