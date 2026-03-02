"""
Kafka Event Bus Service
Central message broker for event-driven architecture
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import asyncio

app = FastAPI(title="Kafka Event Bus")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# In-memory event store (replace with Kafka in production)
# For demo: using asyncio for pub/sub simulation
event_store: Dict[str, List[dict]] = {}
subscribers: Dict[str, List[callable]] = {}


# ============ Models ============

class Event(BaseModel):
    type: str  # payment.completed, order.created, etc.
    payload: Dict[str, Any]
    source: str  # which service
    timestamp: str = datetime.utcnow().isoformat()
    correlation_id: Optional[str] = None


class EventSubscription(BaseModel):
    event_type: str
    callback_url: str


# ============ Topics ============

TOPICS = {
    # Payments
    "payment.initiated": "Payment started",
    "payment.completed": "Payment successful",
    "payment.failed": "Payment failed",
    "payment.refunded": "Payment refunded",
    
    # Orders
    "order.created": "New order placed",
    "order.paid": "Order paid",
    "order.shipped": "Order shipped",
    "order.delivered": "Order delivered",
    "order.completed": "Order completed",
    "order.disputed": "Order disputed",
    
    # Members
    "member.joined": "New member joined",
    "member.left": "Member removed",
    
    # Contributions
    "contribution.created": "New contribution",
    
    # Loans
    "loan.approved": "Loan approved",
    "loan.disbursed": "Loan disbursed",
    "loan.repaid": "Loan repayment received",
    
    # Notifications
    "notification.send": "Send notification",
    
    # System
    "system.error": "System error"
}


# ============ Health ============

@app.get("/health")
def health():
    return {"status": "healthy", "service": "kafka", "topics": len(TOPICS)}


@app.get("/topics")
def list_topics():
    return {"topics": [{"name": k, "description": v} for k, v in TOPICS.items()]}


# ============ Publish Events ============

@app.post("/events/publish")
def publish_event(event: Event):
    """Publish an event to Kafka (simulated)"""
    topic = event.type
    
    # Store event
    if topic not in event_store:
        event_store[topic] = []
    
    event_data = event.dict()
    event_store[topic].append(event_data)
    
    # In production: would send to Kafka
    # producer.send(topic, event.dict())
    
    return {
        "status": "published",
        "topic": topic,
        "timestamp": event.timestamp
    }


@app.post("/events/publish/batch")
def publish_events(events: List[Event]):
    """Publish multiple events"""
    results = []
    
    for event in events:
        topic = event.type
        if topic not in event_store:
            event_store[topic] = []
        event_store[topic].append(event.dict())
        results.append({"topic": topic, "status": "published"})
    
    return {"sent": len(results), "results": results}


# ============ Subscribe ============

@app.post("/events/subscribe")
def subscribe(event_type: str, callback_url: str):
    """Subscribe to an event type"""
    if event_type not in subscribers:
        subscribers[event_type] = []
    
    if callback_url not in subscribers[event_type]:
        subscribers[event_type].append(callback_url)
    
    return {"status": "subscribed", "event_type": event_type}


@app.get("/events/subscribe")
def list_subscriptions():
    return {"subscriptions": subscribers}


# ============ Consume Events ============

@app.get("/events/{event_type}")
def get_events(event_type: str, limit: int = 50):
    """Get events of a specific type"""
    events = event_store.get(event_type, [])
    return events[-limit:]


@app.get("/events")
def get_all_events(limit: int = 100):
    """Get all events"""
    all_events = []
    for events in event_store.values():
        all_events.extend(events)
    
    # Sort by timestamp
    all_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return all_events[:limit]


# ============ Event Processing Patterns ============

@app.get("/patterns")
def get_processing_patterns():
    """Common event processing patterns"""
    return {
        "pub_sub": "One event → Multiple consumers",
        "event_sourcing": "Store all events for replay",
        "cqrs": "Separate read/write models",
        "saga": "Distributed transactions via events",
        "cdc": "Change data capture"
    }


# ============ Example: Order Flow ============

@app.post("/examples/order-flow")
def example_order_flow(order_id: str, buyer_id: str, amount: float):
    """Example: Complete order flow via events"""
    
    events = [
        Event(type="order.created", payload={"order_id": order_id, "buyer_id": buyer_id, "amount": amount}, source="marketplace"),
        Event(type="payment.initiated", payload={"order_id": order_id, "amount": amount}, source="payments"),
        Event(type="payment.completed", payload={"order_id": order_id, "amount": amount, "mpesa_code": "XXX"}, source="payments"),
        Event(type="order.paid", payload={"order_id": order_id}, source="marketplace"),
        Event(type="notification.send", payload={"user_id": buyer_id, "title": "Order Paid", "body": f"Order {order_id} paid"}, source="notifications"),
    ]
    
    for event in events:
        topic = event.type
        if topic not in event_store:
            event_store[topic] = []
        event_store[topic].append(event.dict())
    
    return {"status": "flow_completed", "events": len(events)}


# ============ Kafka Config (for production) ============

KAFKA_CONFIG = {
    "bootstrap_servers": ["kafka:9092"],
    "topics": list(TOPICS.keys()),
    "consumer_groups": {
        "notifications": ["notifications-service"],
        "analytics": ["analytics-service"],
        "payments": ["payments-service"],
        "marketplace": ["marketplace-service"]
    }
}


@app.get("/config")
def get_kafka_config():
    """Kafka configuration for services"""
    return KAFKA_CONFIG


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9092)
