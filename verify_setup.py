import subprocess
import sys

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

checks = [
    ("Python version", "uv run python -c 'import sys; print(sys.version)'"),
    ("Minikube status", "minikube status"),
    ("Kubectl access", "kubectl cluster-info"),
    ("Helm version", "helm version"),
    ("Prometheus pods", "kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus"),
]

print("Running setup verification...")
all_ok = True

for check_name, cmd in checks:
    success, stdout, stderr = run_cmd(cmd)
    if success:
        print(f"✅ {check_name}: OK")
        if stdout:
            print(f"   Output: {stdout.strip()}")
    else:
        print(f"❌ {check_name}: FAILED")
        if stderr:
            print(f"   Error: {stderr.strip()}")
        all_ok = False

if all_ok:
    print("\n🎉 All prerequisites are set up correctly!")
else:
    print("\n⚠️  Some prerequisites failed. Please check the errors above.")
    sys.exit(1)