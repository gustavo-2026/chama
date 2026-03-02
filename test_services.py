#!/usr/bin/env python3
"""
Chama Microservices Test Script
Tests all microservice endpoints
"""
import requests
import json
import time
import sys

BASE_URLS = {
    "core": "http://localhost:8001",
    "marketplace": "http://localhost:8002", 
    "payments": "http://localhost:8003",
    "notifications": "http://localhost:8004",
    "messaging": "http://localhost:8005",
    "kafka": "http://localhost:9093"
}

def print_result(name, response):
    """Print test result"""
    status = "✅" if response.status_code < 400 else "❌"
    print(f"{status} {name}: {response.status_code}")
    if response.status_code >= 400:
        print(f"   Error: {response.text[:100]}")

def test_health_checks():
    """Test health endpoints"""
    print("\n=== Health Checks ===")
    for service, url in BASE_URLS.items():
        try:
            r = requests.get(f"{url}/health", timeout=2)
            print_result(f"{service} health", r)
        except Exception as e:
            print(f"❌ {service} health: Connection failed - {e}")

def test_core_service():
    """Test Core Banking Service"""
    print("\n=== Core Service ===")
    base = BASE_URLS["core"]
    
    # Create member
    r = requests.post(f"{base}/members", json={
        "phone": "254712345678",
        "name": "Test Member",
        "email": "test@chama.co.ke",
        "organization_id": "org_test",
        "role": "MEMBER"
    })
    print_result("Create member", r)
    member_id = r.json().get("id") if r.status_code == 200 else "mem_test"
    
    # List members
    r = requests.get(f"{base}/members?org_id=org_test")
    print_result("List members", r)
    
    # Create contribution
    r = requests.post(f"{base}/contributions", json={
        "member_id": member_id,
        "amount": 1000,
        "method": "CASH"
    })
    print_result("Create contribution", r)
    
    # Get contributions
    r = requests.get(f"{base}/contributions/member/{member_id}")
    print_result("Get member contributions", r)
    
    # Get treasury
    r = requests.get(f"{base}/treasury/org_test")
    print_result("Get treasury", r)

def test_marketplace_service():
    """Test Marketplace Service"""
    print("\n=== Marketplace Service ===")
    base = BASE_URLS["marketplace"]
    
    # Create listing
    r = requests.post(f"{base}/listings", json={
        "title": "Test Product",
        "description": "A test product",
        "category": "PRODUCTS",
        "price": 5000
    })
    print_result("Create listing", r)
    listing_id = r.json().get("id") if r.status_code == 200 else "lst_test"
    
    # Search listings
    r = requests.get(f"{base}/listings?category=PRODUCTS")
    print_result("Search listings", r)
    
    # Create order
    r = requests.post(f"{base}/orders", json={
        "listing_id": listing_id,
        "quantity": 1
    })
    print_result("Create order", r)
    order_id = r.json().get("id") if r.status_code == 200 else "ord_test"
    
    # Get order
    r = requests.get(f"{base}/orders/{order_id}")
    print_result("Get order", r)
    
    # Mark as paid (escrow)
    r = requests.post(f"{base}/orders/{order_id}/paid")
    print_result("Mark paid (escrow)", r)
    
    # Ship order
    r = requests.post(f"{base}/orders/{order_id}/ship")
    print_result("Ship order", r)
    
    # Mark delivered
    r = requests.post(f"{base}/orders/{order_id}/delivered")
    print_result("Mark delivered", r)
    
    # Confirm delivery (release escrow)
    r = requests.post(f"{base}/orders/{order_id}/confirm")
    print_result("Confirm delivery", r)

def test_payments_service():
    """Test Payments Service"""
    print("\n=== Payments Service ===")
    base = BASE_URLS["payments"]
    
    # Get wallet
    r = requests.get(f"{base}/wallet/test_member")
    print_result("Get wallet", r)
    
    # Deposit to wallet
    r = requests.post(f"{base}/wallet/deposit", json={
        "amount": 5000,
        "member_id": "test_member"
    })
    print_result("Wallet deposit", r)
    
    # Get providers
    r = requests.get(f"{base}/providers")
    print_result("Get providers", r)
    
    # Note: STK Push requires M-Pesa credentials
    # r = requests.post(f"{base}/mpesa/stk-push", json={
    #     "amount": 100,
    #     "phone": "254712345678",
    #     "reference": "test_001"
    # })
    # print_result("STK Push", r)

def test_notifications_service():
    """Test Notifications Service"""
    print("\n=== Notifications Service ===")
    base = BASE_URLS["notifications"]
    
    # Send in-app notification
    r = requests.post(f"{base}/in-app/send", json={
        "user_id": "test_user",
        "title": "Test Notification",
        "body": "This is a test"
    })
    print_result("Send notification", r)
    
    # Get notifications
    r = requests.get(f"{base}/in-app/test_user")
    print_result("Get notifications", r)
    
    # Register push token
    r = requests.post(f"{base}/push/register", json={
        "user_id": "test_user",
        "token": "test_token_123",
        "platform": "android"
    })
    print_result("Register push token", r)
    
    # Send push notification
    r = requests.post(f"{base}/push/send", json={
        "user_id": "test_user",
        "title": "Push Test",
        "body": "Push notification test"
    })
    print_result("Send push", r)

def test_messaging_service():
    """Test Messaging Service"""
    print("\n=== Messaging Service ===")
    base = BASE_URLS["messaging"]
    
    # Create conversation
    r = requests.post(f"{base}/conversations", params={
        "member1_id": "mem_1",
        "member2_id": "mem_2"
    })
    print_result("Create conversation", r)
    conv_id = r.json().get("id") if r.status_code == 200 else "conv_test"
    
    # Get user conversations
    r = requests.get(f"{base}/conversations/mem_1")
    print_result("Get conversations", r)
    
    # Send message
    r = requests.post(f"{base}/conversations/{conv_id}/messages", json={
        "sender_id": "mem_1",
        "content": "Hello from test!"
    })
    print_result("Send message", r)
    
    # Get messages
    r = requests.get(f"{base}/conversations/{conv_id}/messages")
    print_result("Get messages", r)
    
    # Get unread count
    r = requests.get(f"{base}/unread/mem_1")
    print_result("Get unread", r)

def test_kafka_event_bus():
    """Test Kafka Event Bus"""
    print("\n=== Kafka Event Bus ===")
    base = BASE_URLS["kafka"]
    
    # Get topics
    r = requests.get(f"{base}/topics")
    print_result("List topics", r)
    
    # Publish event
    r = requests.post(f"{base}/events/publish", json={
        "type": "order.created",
        "payload": {"order_id": "ord_test", "amount": 5000},
        "source": "test-script"
    })
    print_result("Publish event", r)
    
    # Get events
    r = requests.get(f"{base}/events/order.created")
    print_result("Get order events", r)
    
    # Test order flow
    r = requests.get(f"{base}/examples/order-flow?order_id=test_123&buyer_id=mem_1&amount=1000")
    # Get all events
    r = requests.get(f"{base}/events?limit=10")
    print_result("Get all events", r)

def test_end_to_end_flow():
    """Test complete end-to-end flow"""
    print("\n=== End-to-End Flow Test ===")
    
    # 1. Create member
    r = requests.post(f"{BASE_URLS['core']}/members", json={
        "phone": "254799999999",
        "name": "E2E Test User",
        "email": "e2e@test.com",
        "organization_id": "org_e2e",
        "role": "MEMBER"
    })
    print_result("1. Create member", r)
    member_id = r.json().get("id") if r.status_code == 200 else "mem_e2e"
    
    # 2. Create contribution
    r = requests.post(f"{BASE_URLS['core']}/contributions", json={
        "member_id": member_id,
        "amount": 5000,
        "method": "MPESA"
    })
    print_result("2. Create contribution", r)
    
    # 3. Create marketplace listing
    r = requests.post(f"{BASE_URLS['marketplace']}/listings", json={
        "title": "E2E Test Product",
        "description": "Testing E2E flow",
        "category": "PRODUCTS",
        "price": 3000
    })
    print_result("3. Create listing", r)
    listing_id = r.json().get("id") if r.status_code == 200 else "lst_e2e"
    
    # 4. Create order
    r = requests.post(f"{BASE_URLS['marketplace']}/orders", json={
        "listing_id": listing_id,
        "quantity": 1
    })
    print_result("4. Create order", r)
    order_id = r.json().get("id") if r.status_code == 200 else "ord_e2e"
    
    # 5. Pay (escrow)
    r = requests.post(f"{BASE_URLS['marketplace']}/orders/{order_id}/paid")
    print_result("5. Payment (escrow)", r)
    
    # 6. Ship
    r = requests.post(f"{BASE_URLS['marketplace']}/orders/{order_id}/ship")
    print_result("6. Ship order", r)
    
    # 7. Deliver
    r = requests.post(f"{BASE_URLS['marketplace']}/orders/{order_id}/delivered")
    print_result("7. Deliver order", r)
    
    # 8. Confirm (release escrow)
    r = requests.post(f"{BASE_URLS['marketplace']}/orders/{order_id}/confirm")
    print_result("8. Confirm (release escrow)", r)
    
    # 9. Send notification
    r = requests.post(f"{BASE_URLS['notifications']}/in-app/send", json={
        "user_id": member_id,
        "title": "Order Completed!",
        "body": f"Your order {order_id} is complete"
    })
    print_result("9. Send notification", r)
    
    # 10. Publish event
    r = requests.post(f"{BASE_URLS['kafka']}/events/publish", json={
        "type": "order.completed",
        "payload": {"order_id": order_id, "member_id": member_id},
        "source": "e2e-test"
    })
    print_result("10. Publish event", r)
    
    print("\n" + "="*50)
    print("E2E Flow Complete!")
    print("="*50)

def main():
    print("="*50)
    print("Chama Microservices Test Suite")
    print("="*50)
    
    # Check which services are running
    print("\nChecking available services...")
    available = []
    for service, url in BASE_URLS.items():
        try:
            r = requests.get(f"{url}/health", timeout=2)
            if r.status_code == 200:
                available.append(service)
                print(f"  ✅ {service}: {url}")
        except:
            print(f"  ❌ {service}: Not reachable")
    
    if not available:
        print("\nNo services running! Start services first:")
        print("  cd services/core-service && python main.py")
        print("  cd services/marketplace-service && python main.py")
        print("  ...")
        sys.exit(1)
    
    print(f"\nTesting {len(available)} services: {', '.join(available)}")
    
    # Run tests
    test_health_checks()
    
    if "core" in available:
        test_core_service()
    
    if "marketplace" in available:
        test_marketplace_service()
    
    if "payments" in available:
        test_payments_service()
    
    if "notifications" in available:
        test_notifications_service()
    
    if "messaging" in available:
        test_messaging_service()
    
    if "kafka" in available:
        test_kafka_event_bus()
    
    # Full E2E test if all services available
    if set(["core", "marketplace", "notifications", "kafka"]).issubset(set(available)):
        test_end_to_end_flow()
    
    print("\n" + "="*50)
    print("Test Suite Complete!")
    print("="*50)

if __name__ == "__main__":
    main()
