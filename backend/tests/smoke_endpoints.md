# Swagger smoke tests

## events
- GET /api/v1/events
- GET /api/v1/events/{event_id}
- GET /api/v1/events/code/{event_code}
- GET /api/v1/events/hot-near-you?city=Tokyo
- GET /api/v1/events/recommended?user_id=<user_uuid>

## bookings
POST /api/v1/bookings
```json
{
  "user_id": "<user_uuid>",
  "event_id": "<event_uuid>",
  "quantity": 2,
  "unit_price": 6800,
  "currency": "JPY",
  "payment_method": "mock_card",
  "payment_ref": "mock-pay-001",
  "device_id": "ipad-test",
  "ip_address": "127.0.0.1"
}
```

POST /api/v1/bookings/{booking_id}/confirm
```json
{
  "payment_ref": "mock-pay-001",
  "paid_amount": 13600
}
```

POST /api/v1/bookings/{booking_id}/cancel
```json
{
  "reason": "user requested cancellation"
}
```

## tickets
- GET /api/v1/tickets?user_id=<user_uuid>
- GET /api/v1/tickets/{ticket_id}
- GET /api/v1/tickets/{ticket_id}/qr
POST /api/v1/tickets/{ticket_id}/check-in
```json
{
  "scanner_user_id": "<staff_uuid>",
  "gate_code": "gate-a"
}
```

## chat
- GET /api/v1/chat/events/{event_id}/room
- GET /api/v1/chat/events/{event_id}/messages
POST /api/v1/chat/events/{event_id}/messages
```json
{
  "user_id": "<user_uuid>",
  "content": "Can't wait for tonight!"
}
```
