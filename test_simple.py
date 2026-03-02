#!/usr/bin/env python3
"""Simple test - just health checks"""
import requests

services = {
    "core": "http://localhost:8001",
    "marketplace": "http://localhost:8002",
    "payments": "http://localhost:8003",
    "notifications": "http://localhost:8004",
    "messaging": "http://localhost:8005",
    "kafka": "http://localhost:9093"
}

print("=== Microservices Health Check ===")
all_ok = True
for name, url in services.items():
    try:
        r = requests.get(f"{url}/health", timeout=2)
        if "healthy" in r.text:
            print(f"✅ {name}: {r.json().get('service', 'ok')}")
        else:
            print(f"❌ {name}: {r.text}")
            all_ok = False
    except Exception as e:
        print(f"❌ {name}: {e}")
        all_ok = False

print()
if all_ok:
    print("🎉 All 6 microservices running!")
else:
    print("Some services need attention")
