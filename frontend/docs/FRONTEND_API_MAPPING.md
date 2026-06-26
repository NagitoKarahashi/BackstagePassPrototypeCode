# Frontend API Mapping

## Login
- Supabase auth in browser
- After successful login, call `POST /profiles/bootstrap`
- Then fetch `GET /profiles/me`

## Dashboard
- `GET /me/overview`
- Optional later: `GET /events/hot-near-you?city=...`
- Optional later: `GET /events/recommended?user_id=...`

## Events list
- `GET /events`
- Supported filters now: `q`, `city`, `genre`, `artist`, `country`, `date_from`, `date_to`, `only_available`, `limit`, `offset`

## Event detail
- `GET /events/{event_id}`

## Purchase
- `POST /orders/create`
- Request body: `{ user_id, event_id, quantity }`
- `POST /orders/{order_id}/pay`

## Wallet
- `GET /tickets/my?user_id=...`
- `GET /tickets/{ticket_id}`
- `GET /tickets/{ticket_id}/qr`

## Chat
- `GET /chat/events/{event_uuid}/room`
- `GET /chat/events/{event_uuid}/messages`
- `POST /chat/events/{event_uuid}/messages`
- Request body: `{ user_id, content }`

## Profile
- `GET /profiles/me`
- `PATCH /profiles/me`
- `GET /me/history`

## Rewards
- `GET /rewards/overview`
- `GET /rewards/checkin-status`
- `POST /rewards/checkin`
- `GET /rewards/missions`
- `POST /rewards/missions/{mission_id}/start`
- `POST /rewards/missions/{mission_id}/claim`
- `GET /rewards/summary`
- `GET /rewards/ledger`
- `GET /rewards/badges`
- `GET /rewards/leaderboard`
- `GET /rewards/catalog`
- `POST /rewards/redeem/{reward_id}`
- `GET /rewards/my-redemptions`

## Artists
- `GET /artists/follows`
- `POST /artists/{artist_id}/follow`
- `DELETE /artists/{artist_id}/follow`

## Notifications
- `GET /notifications/my?user_id=...`

## Mock-first areas
- Rich artist detail content
- Organizer view
- Real-time chat
- Fraud appeal UI
- Blockchain wallet / NFT layer
