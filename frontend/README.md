# Backstage Pass Frontend Starter

This starter is aligned to your current FastAPI backend:
- API base path: `/api/v1`
- Auth: Supabase bearer token
- Current-user endpoints already supported for `profiles/me`, `me/overview`, `rewards/*`
- Some endpoints still require explicit IDs in params/body, especially `orders`, `tickets/my`, `chat message post`, and `notifications/my`

## What is included
- Next.js App Router + TypeScript starter
- Phase 1 page skeletons
- Shared API client with bearer token injection
- Supabase browser client helper
- Simple, teammate-friendly folder structure
- API wrappers for events / orders / tickets / chat / profile / me / rewards / artists / notifications
- Demo notes for real vs mock areas

## Install
```bash
cd ./backstage-pass-frontend-starter
npm install
npm run dev
```

## Environment
Copy `.env.example` to `.env.local` and fill in values.

## Real API coverage now
### Real now
- Login session handling (Supabase)
- `/profiles/bootstrap`
- `/profiles/me`
- `/me/overview`
- `/me/history`
- `/events`
- `/events/{eventId}`
- `/events/hot-near-you`
- `/events/recommended`
- `/orders/create`
- `/orders/{orderId}/pay`
- `/tickets/my`
- `/tickets/{ticketId}`
- `/tickets/{ticketId}/qr`
- `/chat/events/{eventUuid}/room`
- `/chat/events/{eventUuid}/messages`
- `/rewards/*`
- `/artists/follows`
- `/artists/{artistId}/follow`
- `/notifications/my`

### Mock or half-real for now
- Artist detail content (bio / stats / rich upcoming module): mock shell only
- Full organizer dashboard: not included
- Real-time chat: not included
- Fraud appeal UI: not included
- NFT / blockchain wallet UI: not included in Phase 1 starter

## Important backend alignment notes
1. `orders/create` still requires `{ user_id, event_id, quantity }` in body.
2. `tickets/my` still requires `user_id` query.
3. Chat uses `event_uuid` in URL and `user_id` in post body.
4. `notifications/my` still requires `user_id` query.
5. Event discovery uses `event.id` for detail pages.

## Suggested build order
1. Finish `.env.local`
2. Verify login and token retrieval
3. Test `/profiles/bootstrap` after login
4. Build dashboard
5. Build events list + detail
6. Build order + wallet flow
7. Build chat flow
8. Build profile + rewards
9. Build artist following + notifications


## Fastest fix for the current runtime error
Create `.env.local` in the frontend root:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_SUPABASE_URL=YOUR_SUPABASE_PROJECT_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
```

Then restart the frontend dev server:

```bash
npm run dev
```

If login still does not complete, make sure Supabase Auth redirect URLs include:
- `http://localhost:3000/dashboard`
- `http://127.0.0.1:3000/dashboard`

The protected layout in this updated starter now:
- blocks protected pages when env is missing
- redirects to `/login` when no session exists
- tries `/profiles/bootstrap` automatically after login
