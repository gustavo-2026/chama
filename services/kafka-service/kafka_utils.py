"""
Kafka Producer/Consumer Utilities
Add to each microservice
"""
from typing import Dict, Any, Callable, Optional
import requests
import json
import os

# Kafka service URL
KAFKA_SERVICE = os.getenv("KAFKA_SERVICE_URL", "http://localhost:9092")


class EventProducer:
    """Publish events to Kafka"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.base_url = KAFKA_SERVICE
    
    def publish(self, event_type: str, payload: Dict[str, Any], correlation_id: Optional[str] = None):
        """Publish event to Kafka"""
        event = {
            "type": event_type,
            "payload": payload,
            "source": self.service_name,
            "correlation_id": correlation_id
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/events/publish",
                json=event,
                timeout=5
            )
            return response.json()
        except Exception as e:
            print(f"Failed to publish event: {e}")
            return {"status": "failed", "error": str(e)}
    
    def publish_batch(self, events: list):
        """Publish multiple events"""
        try:
            response = requests.post(
                f"{self.base_url}/events/publish/batch",
                json=events,
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f"Failed to publish events: {e}")
            return {"status": "failed", "error": str(e)}


class EventConsumer:
    """Consume events from Kafka"""
    
    def __init__(self, service_name: str, event_types: list):
        self.service_name = service_name
        self.event_types = event_types
        self.handlers: Dict[str, Callable] = {}
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register handler for event type"""
        self.handlers[event_type] = handler
    
    def subscribe(self):
        """Subscribe to event types"""
        import requests
        for event_type in self.event_types:
            try:
                requests.post(
                    f"{KAFKA_SERVICE}/events/subscribe",
                    params={"event_type": event_type, "callback_url": f"{self.service_name}/events/{event_type}"},
                    timeout=5
                )
            except Exception as e:
                print(f"Failed to subscribe to {event_type}: {e}")
    
    def poll(self):
        """Poll for new events"""
        import requests
        for event_type in self.event_types:
            try:
                response = requests.get(
                    f"{KAFKA_SERVICE}/events/{event_type}",
                    params={"limit": 10},
                    timeout=5
                )
                events = response.json()
                
                handler = self.handlers.get(event_type)
                if handler and events:
                    for event in events:
                        handler(event)
            except Exception as e:
                print(f"Failed to poll {event_type}: {e}")


# Convenience methods for common events

def publish_payment_event(producer: EventProducer, event_type: str, data: dict):
    """Publish payment event"""
    return producer.publish(f"payment.{event_type}", data)


def publish_order_event(producer: EventProducer, event_type: str, data: dict):
    """Publish order event"""
    return producer.publish(f"order.{event_type}", data)


def publish_member_event(producer: EventProducer, event_type: str, data: dict):
    """Publish member event"""
    return producer.publish(f"member.{event_type}", data)


def publish_notification_event(producer: EventProducer, data: dict):
    """Publish notification event"""
    return producer.publish("notification.send", data)


# Example Usage in a Service

"""
# In your service:

from kafka_utils import EventProducer, publish_order_event

# Initialize producer
producer = EventProducer("marketplace-service")

# When order is created:
publish_order_event(producer, "created", {
    "order_id": "ord_123",
    "buyer_id": "mem_456",
    "amount": 5000
})

# When payment completes:
publish_order_event(producer, "paid", {
    "order_id": "ord_123"
})
"""
