# Chama Microservices

Event-driven microservices architecture with Kafka event bus.

## Services

| Service | Port | Description |
|---------|------|-------------|
| Core | 8001 | Members, Contributions, Loans, Treasury |
| Marketplace | 8002 | Listings, Orders, Reviews, Escrow |
| Payments | 8003 | M-Pesa, Pesapal, Wallet |
| Notifications | 8004 | Push, SMS, Email, In-App |
| Messaging | 8005 | Real-time WebSocket chat |
| **Kafka** | 9092 | Event Bus |

## Architecture

```
                    ┌──────────────┐
                    │ API Gateway  │
                    │   (Nginx)   │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│     Core      │ │  Marketplace  │ │   Payments    │
│   Service     │ │   Service     │ │   Service     │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │     Kafka Event Bus      │
              │  (Event Publishing)      │
              └────────────┬────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Notifications │ │  Analytics    │ │    Audit      │
│   Service    │ │   Service     │ │    Service    │
└───────────────┘ └───────────────┘ └───────────────┘
```

## Event Flow

```
Order Created → Kafka → Notifications (send SMS)
                      → Analytics (track metrics)
                      → Payments (process)
                      → Audit (log)
```

## Event Topics

| Topic | Description |
|-------|-------------|
| `payment.initiated` | Payment started |
| `payment.completed` | Payment successful |
| `order.created` | New order |
| `order.paid` | Order paid |
| `order.shipped` | Order shipped |
| `member.joined` | New member |
| `loan.approved` | Loan approved |

## Quick Start

```bash
# Docker Compose
docker-compose -f docker/docker-compose.yml up

# Or run individually
cd services/kafka-service && python main.py
cd services/core-service && python main.py
cd services/marketplace-service && python main.py
cd services/payments-service && python main.py
cd services/notifications-service && python main.py
```

## Environment

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/chama
KAFKA_SERVICE_URL=http://localhost:9092

# M-Pesa
MPESA_SHORTCODE=123456
MPESA_CONSUMER_KEY=xxx

# Pesapal
PESAPAL_CONSUMER_KEY=xxx
```

## API Examples

### Publish Event
```bash
curl -X POST http://localhost:9092/events/publish -H "Content-Type: application/json" -d '{
  "type": "order.created",
  "payload": {"order_id": "ord_1", "amount": 5000},
  "source": "marketplace-service"
}'
```

### Subscribe to Events
```bash
curl -X POST "http://localhost:9092/events/subscribe?event_type=order.created&callback_url=http://notifications-service"
```

### Get Events
```bash
curl http://localhost:9092/events/order.created
```

### Order Flow Example
```bash
curl -X POST http://localhost:9092/examples/order-flow -d '{"order_id":"ord_123","buyer_id":"mem_1","amount":5000}'
```
