# Backstage Pass backend scaffold

This is a modular FastAPI + Supabase backend scaffold aligned to your Phase 1 API priorities.

## Run

```bash
cd backstage_pass_backend
python -m venv .venv
source .venv/bin/activate  # Windows Git Bash
pip install -r requirements_backend.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Main routes

- `GET /health`
- `GET /api/v1/events`
- `GET /api/v1/events/{event_id}`
- `GET /api/v1/events/code/{event_code}`
- `GET /api/v1/events/hot-near-you`
- `GET /api/v1/events/recommended?user_id=...`
- `POST /api/v1/bookings`
- `POST /api/v1/bookings/{booking_id}/confirm`
- `POST /api/v1/bookings/{booking_id}/cancel`
- `GET /api/v1/tickets?user_id=...`
- `GET /api/v1/tickets/{ticket_id}`
- `GET /api/v1/tickets/{ticket_id}/qr`
- `POST /api/v1/tickets/{ticket_id}/check-in`
- `GET /api/v1/chat/events/{event_id}/room`
- `GET /api/v1/chat/events/{event_id}/messages`
- `POST /api/v1/chat/events/{event_id}/messages`
- `GET /api/v1/rewards/ledger?user_id=...`
- `GET /api/v1/rewards/badges?user_id=...`
- `GET /api/v1/rewards/leaderboard`
- `GET /api/v1/artists/{artist_id}`
- `GET /api/v1/artists/{artist_id}/events`
- `POST /api/v1/artists/{artist_id}/follow?user_id=...`

## Expected tables

- `events`
- `orders`
- `tickets`
- `chat_rooms`
- `chat_messages`
- `reward_ledger`
- `user_badges`
- `artists`
- `artist_follows`
- `profiles`

## Notes

- `events.id` is treated as UUID internal PK.
- `events.event_code` is treated as business identifier.
- Confirm booking reduces `tickets_remaining` and inserts rows into `tickets`.
- Cancel booking restores inventory when the booking was already confirmed.
- Event chat only allows users who own an active ticket or confirmed order for that event.

You may need to adjust column names to match your exact Supabase schema.

git status
git add .
git commit -m "update project"
git push origin main
