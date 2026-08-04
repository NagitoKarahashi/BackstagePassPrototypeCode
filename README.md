# Backstage Pass

Backstage Pass is an AI-assisted, risk-aware, Web3-ready event ticketing prototype developed as a graduation project. It combines event discovery, conversational support, simulated ticket purchasing, a digital ticket wallet, QR check-in, fan engagement, and rule-based fraud controls.

> This is a prototype, not a production ticketing platform. Payments, NFT minting, blockchain transactions, and settlement are simulated.

## Core User Journey

```text
Sign in with Privy
→ Browse or ask about events
→ Confirm a simulated purchase
→ Receive a digital ticket
→ View wallet and QR code
→ Check in, transfer, refund, or list the ticket
```

## Main Features

| Area | Current implementation |
| --- | --- |
| Authentication | Privy login with FastAPI bearer-token validation and profile bootstrap |
| Event discovery | Supabase-backed event list, filters, details, and recommendations |
| AI assistant | English/Chinese handling, spelling normalization, intent classification, TF-IDF + BM25 retrieval, live event search, and structured event responses |
| Chatbot purchase flow | Event selection and order confirmation before any database write; authenticated confirmation uses the existing simulated order and ticket flow |
| Orders and tickets | Atomic order creation, simulated payment, ticket issuance, cancellation, wallet views, and QR payloads |
| Ticket lifecycle | Check-in, transfer, refund, ownership history, and marketplace listing/buy/cancel operations |
| Risk and fraud | Rule-based low/medium/high risk decisions with warnings, review requirements, or blocking |
| Fan engagement | Event chat, rewards, badges, artist follows, notifications, and support enquiries |
| Web3-ready fields | Simulated token ID, contract, chain, mint status, and transaction hash |

## Architecture

```text
Next.js / React frontend
        ↓ Privy access token
FastAPI REST API
        ↓
Supabase / PostgreSQL + transactional RPC functions

Assistant data:
Supabase events + local FAQ/policy knowledge base + TF-IDF/BM25 index
```

## Technology Stack

- Frontend: Next.js 15, React 19, TypeScript, Privy React SDK, Tailwind CSS
- Backend: FastAPI, Python, Pydantic, Supabase Python client
- Database: Supabase PostgreSQL
- Retrieval: scikit-learn TF-IDF, BM25, local FAQ and policy sources
- Deployment: Vercel frontend, Render backend, Supabase data platform

## Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── core/        # Settings, authentication, shared dependencies
│   │   ├── db/          # Supabase client
│   │   ├── routers/     # FastAPI endpoints
│   │   ├── schemas/     # Pydantic request/response models
│   │   ├── services/    # Business logic and database workflows
│   │   └── main.py      # Application entry point
│   ├── data/            # FAQ, policy, and legacy catalogue assets
│   ├── sql/             # Baseline schema and database functions
│   ├── tests/           # Test and smoke-check resources
│   └── requirements.txt
├── frontend/
│   ├── src/app/         # Next.js routes
│   ├── src/components/  # Shared and feature components
│   ├── src/lib/api/     # FastAPI client wrappers
│   └── package.json
└── docs/                # Project, API, database, architecture, and demo notes
```

## Local Setup

### 1. Backend

```bash
cd backend
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install dependencies and create the environment file:

```bash
pip install -r requirements.txt
cp .env.example .env
```

On Windows Command Prompt, use `copy .env.example .env` instead of `cp`.

Required backend configuration:

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_ANON_KEY=
PRIVY_APP_ID=
PRIVY_VERIFICATION_KEY=
CORS_ORIGINS=http://localhost:3000
```

Start the API:

```bash
uvicorn app.main:app --reload
```

- Health check: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
```

Configure the frontend:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_PRIVY_APP_ID=
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

Then run:

```bash
npm run dev
```

Open `http://localhost:3000`.

## Chatbot API

The current assistant reads live event records from Supabase. The legacy `backend/data/events.csv` should not be used as the source of truth for current event availability.

### Ask a question

```http
POST /api/v1/ask
Content-Type: application/json

{
  "question": "Show upcoming events",
  "context": {
    "current_event_id": null
  }
}
```

The response can include `answer`, `intent`, `lang`, `events`, `action`, risk fields, and suggested next actions.

### Confirm a simulated purchase

```http
POST /api/v1/ask/purchase/confirm
Authorization: Bearer <privy_access_token>
Content-Type: application/json

{
  "event_id": "<event_uuid>",
  "quantity": 2,
  "lang": "en"
}
```

The assistant never creates an order from the initial natural-language request. The authenticated confirmation endpoint rechecks event availability, stock, user identity, and risk before creating and paying the simulated order.

## Database Requirements

The deployed Supabase schema is the runtime source of truth. The current backend expects tables for profiles, events, orders, tickets, check-in logs, chat, rewards, marketplace, notifications, artist follows, support enquiries, and risk or ownership history.

Transaction-sensitive flows depend on PostgreSQL functions including:

- `create_order_atomic`
- `pay_order_and_issue_tickets`
- `cancel_order_and_restore_stock`
- `refund_ticket_atomic`

Before recreating the environment, verify that `backend/sql/` matches the deployed schema and RPC definitions.

## Verification

Recommended checks before deployment:

```bash
# Backend
python -m compileall app

# Frontend
npm run build
```

After deployment, verify `/health`, `/docs`, `/api/v1/events`, `/api/v1/ask`, and the authenticated purchase-confirmation flow.

## Known Limitations

- Payment and blockchain operations are mock implementations.
- NFT-style metadata is stored in the application database; no real smart contract is called.
- Event chat is request/response based rather than real-time.
- The deployed Supabase schema and RPC functions may be newer than the baseline SQL files in this repository.
- The serialized TF-IDF store is version-sensitive; keep its scikit-learn/joblib versions compatible or rebuild the index.
- Security, concurrency, load, and recovery testing must be expanded before production use.

## Documentation

The root README is intentionally brief. Detailed architecture, endpoint inventory, data contracts, workflows, deployment notes, and maintenance risks are covered in the separate **Backstage Pass Technical Documentation**. The `docs/` folder also contains project overview, API, database, UI mapping, demo, status, and architecture notes.

Stress-test materials are maintained separately in [BackstagePassStresstest](https://github.com/NagitoKarahashi/BackstagePassStresstest).

## Academic Use

This repository is provided for code review, demonstration, and academic assessment. It does not contain production credentials or real payment and blockchain integrations.

## Author

Tan Zhi

Dissertation project: **Backstage Pass — AI + Web3-ready Event Ticketing and Fan Engagement Platform**
