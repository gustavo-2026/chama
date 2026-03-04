# Chama Microservices Architecture

Comprehensive documentation for the Chama platform microservices.

---

## Overview

The Chama platform uses a **microservices architecture** with 6 services:

| Service | Port | Purpose |
|---------|------|---------|
| Core | 8001 | Members, Contributions, Loans, Treasury |
| Marketplace | 8002 | Listings, Orders, Escrow |
| Payments | 8003 | M-Pesa, Pesapal, Wallet, Escrow |
| Notifications | 8004 | Push, SMS, Email, In-App |
| Messaging | 8005 | Real-time WebSocket chat |
| Kafka Event Bus | 9093 | Event-driven communication |

---

## Architecture Diagram

```
                    ┌─────────────────┐
                    │   API Gateway   │
                    │    (Nginx)     │
                    └────────┬────────┘
                             │
        ┌──────────┬─────────┼─────────┬──────────┐
        │          │         │         │          │
        ▼          ▼         ▼         ▼          ▼
   ┌────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌────────┐
   │  Core │ │Marketplace│ │Payments│ │ Notif   │ │ Msg   │
   │ 8001  │ │  8002    │ │  8003  │ │  8004   │ │ 8005  │
   └───┬────┘ └────┬─────┘ └───┬────┘ └───┬─────┘ └───┬────┘
       │           │            │          │            │
       └───────────┴─────┬──────┴──────────┴────────────┘
                        │
                 ┌──────▼──────┐
                 │    Kafka    │
                 │ Event Bus   │
                 │   9093      │
                 └─────────────┘
                        │
                 ┌──────▼──────┐
                 │  PostgreSQL │
                 │   5432      │
                 └─────────────┘
```

---

## Core Service (Port 8001)

**Purpose**: Core banking operations for chama management

### Features

- **Member Management**: Join, leave, roles (chairperson, secretary, treasurer, member)
- **Contributions**: Track member payments (monthly, daily, custom)
- **Loans**: Issue loans, track repayments, interest calculations
- **Treasury**: Track chama balance, dividends

### Data Models

```python
Member:
  - id, phone, name, email
  - organization_id (chama_id)
  - role: CHAIRPERSON | SECRETARY | TREASURER | MEMBER
  - status: ACTIVE | INACTIVE | SUSPENDED

Contribution:
  - id, member_id, amount
  - method: CASH | MPESA | BANK
  - status: PENDING | COMPLETED | FAILED

Loan:
  - id, member_id, principal_amount
  - term_months, interest_rate
  - status: PENDING | APPROVED | REJECTED | DISBURSED | REPAID
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/members` | Create member |
| GET | `/members/{chama_id}` | List chama members |
| POST | `/contributions` | Record contribution |
| GET | `/contributions/{chama_id}` | List contributions |
| POST | `/loans` | Apply for loan |
| POST | `/loans/{id}/approve` | Approve loan |
| GET | `/treasury/{chama_id}` | Get chama balance |
| POST | `/dividends/calculate` | Calculate dividends |

### Example: Create Member

```bash
curl -X POST http://localhost:8001/members \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+254712345678",
    "name": "John Doe",
    "email": "john@example.com",
    "organization_id": "chama_001",
    "role": "MEMBER"
  }'
```

---

## Marketplace Service (Port 8002)

**Purpose**: E-commerce marketplace with chama-affiliate system

### Features

- **Listings**: Products, services, jobs, housing
- **Orders**: Full order lifecycle management
- **Escrow**: Funds held until delivery confirmed
- **Affiliate Chamas**: Chamas earn fees on member sales
- **Reviews**: Buyer ratings and reviews

### Data Models

```python
Listing:
  - id, organization_id, member_id
  - title, description, category
  - price, status (ACTIVE | SOLD | HIDDEN)
  - images (JSON array)

Order:
  - id, listing_id, buyer_id, seller_id
  - amount, platform_fee, chama_fee
  - status: PENDING → PAID → SHIPPED → DELIVERED → COMPLETED
  - escrow_status: HOLDING | RELEASED | REFUNDED

Escrow:
  - id, order_id, amount
  - status: PENDING | HELD | RELEASED | DISPUTED
  - release_date (auto-release after 7 days)
```

### Escrow Flow

```
1. Buyer pays → Funds held in escrow
2. Seller ships → Update order status
3. Buyer confirms delivery → Release funds to seller
4. If no confirmation → Auto-release after 7 days
5. Dispute → Admin intervention required
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/listings` | Create listing |
| GET | `/listings` | Search listings |
| POST | `/orders` | Create order |
| POST | `/orders/{id}/pay` | Mark order paid |
| POST | `/orders/{id}/ship` | Mark shipped |
| POST | `/orders/{id}/deliver` | Confirm delivery |
| POST | `/orders/{id}/complete` | Complete (release escrow) |
| POST | `/orders/{id}/dispute` | Open dispute |
| GET | `/escrow/{order_id}` | Get escrow status |

### Example: Create Listing

```bash
curl -X POST http://localhost:8002/listings \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "chama_001",
    "member_id": "member_123",
    "title": "Fresh Farm Produce",
    "description": "Organic vegetables",
    "category": "PRODUCTS",
    "price": 1500.00
  }'
```

---

## Payments Service (Port 8003)

**Purpose**: Payment processing with M-Pesa and Pesapal

### Features

- **M-Pesa Integration**: STK Push (C2B), B2C disbursements
- **Pesapal Integration**: Cards, bank transfers
- **Wallet**: Internal wallet system
- **Unified Checkout**: Single API for all payment methods

### Payment Flow

```
1. User selects payment method
2. Call /checkout → Get payment URL/phone
3. User completes payment on their device
4. Provider calls back → Update payment status
5. Publish event to Kafka → Notify other services
```

### Data Models

```python
Payment:
  - id, member_id, amount
  - provider: MPESA | PESAPAL | WALLET
  - type: CONTRIBUTION | LOAN_REPAYMENT | MARKETPLACE | WITHDRAWAL
  - status: PENDING | COMPLETED | FAILED
  - reference (provider's transaction ID)

Wallet:
  - member_id, balance
  - transactions: list of in/out transactions
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/providers` | List payment providers |
| POST | `/checkout` | Initiate payment |
| POST | `/mpesa/stk-push` | M-Pesa STK Push |
| POST | `/mpesa/callback` | M-Pesa webhook |
| POST | `/pesapal/register-urls` | Register IPN |
| POST | `/pesapal/callback` | Pesapal webhook |
| POST | `/wallet/deposit` | Add to wallet |
| POST | `/wallet/withdraw` | Withdraw from wallet |
| GET | `/wallet/{member_id}` | Get balance |

### M-Pesa STK Push

```bash
curl -X POST http://localhost:8003/mpesa/stk-push \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "254712345678",
    "amount": 1000,
    "reference": "ORDER_123",
    "description": "Payment for order"
  }'
```

### Unified Checkout

```bash
curl -X POST http://localhost:8003/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 5000,
    "provider": "mpesa",
    "type": "CONTRIBUTION",
    "reference": "CONTRIB_001",
    "member_id": "member_123"
  }'
```

### Environment Variables

```bash
MPESA_SHORTCODE=123456
MPESA_CONSUMER_KEY=your_key
MPESA_CONSUMER_SECRET=your_secret
MPESA_PASSKEY=your_passkey
MPESA_ENV=sandbox

PESAPAL_CONSUMER_KEY=your_key
PESAPAL_CONSUMER_SECRET=your_secret
```

---

## Notifications Service (Port 8004)

**Purpose**: Multi-channel notifications

### Features

- **Push Notifications**: Firebase/FCM
- **SMS**: Bulk SMS capabilities
- **Email**: Transactional emails
- **In-App**: Real-time notification center
- **Batch Notifications**: Send to multiple users

### Data Models

```python
Notification:
  - id, user_id, title, body
  - channel: PUSH | SMS | EMAIL | IN_APP
  - status: SENT | FAILED | PENDING
  - created_at

PushToken:
  - user_id, token, platform (android/ios)
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/push/register` | Register FCM token |
| POST | `/send` | Send single notification |
| POST | `/send/batch` | Send to multiple users |
| GET | `/notifications/{user_id}` | Get user notifications |
| PUT | `/notifications/{id}/read` | Mark as read |

### Example: Send Notification

```bash
curl -X POST http://localhost:8004/send \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "member_123",
    "title": "Payment Received",
    "body": "You received KES 5,000",
    "channel": "in_app"
  }'
```

---

## Messaging Service (Port 8005)

**Purpose**: Real-time chat between users

### Features

- **WebSocket**: Real-time bidirectional messaging
- **Typing Indicators**: Show when user is typing
- **Read Receipts**: Track message reads
- **REST API**: Alternative to WebSocket

### WebSocket Connection

```
ws://localhost:8005/ws/{JWT_TOKEN}
```

### Message Format (WebSocket)

```json
// Send message
{
  "type": "message",
  "conversation_id": "conv_123",
  "content": "Hello!"
}

// Receive message
{
  "type": "message",
  "data": {
    "id": "msg_456",
    "conversation_id": "conv_123",
    "sender_id": "member_123",
    "content": "Hello!",
    "created_at": "2026-03-05T10:00:00"
  }
}

// Typing indicator
{
  "type": "typing",
  "sender_id": "member_123",
  "conversation_id": "conv_123"
}

// Read receipt
{
  "type": "read",
  "conversation_id": "conv_123",
  "read_by": "member_456"
}
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | `/ws/{token}` | WebSocket endpoint |
| POST | `/conversations` | Create conversation |
| GET | `/conversations/{user_id}` | List user conversations |
| GET | `/conversations/{id}/messages` | Get messages |
| POST | `/conversations/{id}/messages` | Send message (REST) |
| GET | `/unread/{user_id}` | Unread count |

---

## Kafka Event Bus (Port 9093)

**Purpose**: Event-driven communication between services

### Event Topics

| Category | Event | Description |
|----------|-------|-------------|
| Payments | `payment.initiated` | Payment started |
| | `payment.completed` | Payment successful |
| | `payment.failed` | Payment failed |
| | `payment.refunded` | Payment refunded |
| Orders | `order.created` | New order placed |
| | `order.paid` | Order paid |
| | `order.shipped` | Order shipped |
| | `order.delivered` | Delivered |
| | `order.completed` | Completed |
| | `order.disputed` | Dispute opened |
| Members | `member.joined` | New member |
| | `member.left` | Member removed |
| Loans | `loan.approved` | Loan approved |
| | `loan.disbursed` | Loan disbursed |
| | `loan.repaid` | Repayment received |

### Publishing Events

```bash
curl -X POST http://localhost:9093/events/publish \
  -H "Content-Type: application/json" \
  -d '{
    "type": "payment.completed",
    "source": "payments",
    "payload": {
      "payment_id": "pay_123",
      "amount": 5000,
      "member_id": "member_456"
    },
    "correlation_id": "order_789"
  }'
```

### Subscribing to Events

```bash
curl -X POST http://localhost:9093/events/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "payment.completed",
    "callback_url": "http://localhost:8002/webhooks/payment"
  }'
```

---

## Authentication

All services use JWT tokens:

```bash
# Include in headers
Authorization: Bearer {JWT_TOKEN}

# Token payload
{
  "sub": "member_123",
  "chama_id": "chama_001",
  "role": "MEMBER",
  "exp": 1700000000
}
```

---

## Database

- **PostgreSQL**: `chama_ms` on port 5432
- Each service can use its own database or share
- Password: `postgres`

### Schema

See `seed_data.py` for full schema creation and sample data.

---

## Running the Services

### Start All Services

```bash
cd /home/gustavo/.openclaw/workspace/chama-ms

# Core
python3 services/core-service/main.py &

# Marketplace
python3 services/marketplace-service/main.py &

# Payments
python3 services/payments-service/main.py &

# Notifications
python3 services/notifications-service/main.py &

# Messaging
python3 services/messaging-service/main.py &

# Kafka Event Bus
python3 -m uvicorn services.kafka-service.main:app --port 9093 &
```

### Health Checks

```bash
for port in 8001 8002 8003 8004 8005 9093; do
  curl http://localhost:$port/health
done
```

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/chama_ms

# JWT
SECRET_KEY=change-me-in-production-min-32-characters

# M-Pesa
MPESA_SHORTCODE=123456
MPESA_CONSUMER_KEY=
MPESA_CONSUMER_SECRET=
MPESA_PASSKEY=
MPESA_ENV=sandbox

# Pesapal
PESAPAL_CONSUMER_KEY=
PESAPAL_CONSUMER_SECRET=
```

---

## Future Enhancements

1. **API Gateway**: Nginx or Kong for rate limiting, auth
2. **Service Discovery**: Consul or etcd
3. **Circuit Breaker**: Resilience4j patterns
4. **Distributed Tracing**: Jaeger
5. **Metrics**: Prometheus + Grafana
6. **Real Kafka**: Replace in-memory with actual Kafka cluster
