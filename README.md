# Chama Microservices

Microservices architecture version of the Chama platform.

## Services

| Service | Port | Description |
|---------|------|-------------|
| Core | 8001 | Members, Contributions, Loans, Treasury, Proposals |
| Marketplace | 8002 | Listings, Orders, Reviews, Escrow |
| Payments | 8003 | M-Pesa, Pesapal, Wallet, Escrow |
| Notifications | 8004 | Push, SMS, Email, In-App |
| Messaging | 8005 | Real-time WebSocket chat |

## Quick Start

```bash
# Run all services
docker-compose -f docker/docker-compose.yml up

# Or run individually
cd services/core-service && python main.py
cd services/marketplace-service && python main.py
cd services/payments-service && python main.py
cd services/notifications-service && python main.py
cd services/messaging-service && python main.py
```

## Environment

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/chama
MPESA_SHORTCODE=123456
MPESA_CONSUMER_KEY=xxx
MPESA_CONSUMER_SECRET=xxx
MPESA_PASSKEY=xxx
PESAPAL_CONSUMER_KEY=xxx
PESAPAL_CONSUMER_SECRET=xxx
```

## API Examples

### Create Member
```bash
curl -X POST http://localhost:8001/members -H "Content-Type: application/json" -d '{"phone":"254712345678","name":"John","organization_id":"org_1"}'
```

### Create Listing
```bash
curl -X POST http://localhost:8002/listings -H "Content-Type: application/json" -d '{"title":"Bike for sale","description":"Good condition","category":"PRODUCTS","price":5000}'
```

### Initiate Payment
```bash
curl -X POST http://localhost:8003/mpesa/stk-push -H "Content-Type: application/json" -d '{"amount":1000,"phone":"254712345678","reference":"order_1"}'
```

### Send Notification
```bash
curl -X POST http://localhost:8004/send -H "Content-Type: application/json" -d '{"user_id":"user_1","title":"Hello","body":"Test","channel":"in_app"}'
```
