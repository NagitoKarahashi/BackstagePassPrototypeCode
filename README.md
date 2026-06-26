# Backstage Pass Prototype Code

Backstage Pass is an AI + Web3-inspired event ticketing and fan engagement platform developed as a graduation project prototype.

This repository contains the organized prototype code and supporting documentation for academic review and illustration purposes. It is **not directly connected to the active Vercel or Render deployment repositories**.

## Project Overview

Backstage Pass aims to improve the event ticketing experience by combining concert discovery, digital ticket ownership, fan engagement, AI assistance, and risk-aware ticket operations.

The Phase 1 prototype demonstrates the following core user journey:

```text
Discover Event
→ Ask AI Assistant
→ Buy Ticket
→ Store Ticket in Wallet
→ QR Check-in
→ Fraud Risk Warning
```

Blockchain/NFT functionality is simulated in this prototype stage. The ticket wallet and token-related fields are designed to represent a Web3-style user experience and can be extended into real NFT minting in later phases.

## Key Features

### Event Discovery

Users can browse available events, view event details, and access recommended or popular events.

### Ticket Ordering

The system supports a basic ticket purchase flow, including order creation, payment confirmation, cancellation, and ticket generation.

### Ticket Wallet

Purchased tickets are stored in a digital wallet-style interface. Each ticket can contain NFT-style metadata such as token ID, contract address, chain information, and QR verification payload.

### QR Check-in

The prototype includes a QR-based ticket verification and check-in flow. This is implemented as a mock or prototype-level check-in mechanism for demonstration purposes.

### AI Chatbot Assistant

The AI assistant provides event-related and policy-related support using a retrieval-based approach. It supports FAQ/policy retrieval, intent classification, bilingual query handling, and response generation based on available project data.

### Fan Engagement

The prototype includes user-facing engagement functions such as chat, artist following, rewards, notifications, and user profile-related features.

### Risk / Fraud Detection

The system includes a rule-based risk scoring module for detecting potentially suspicious actions, such as risky ticket transfer, abnormal check-in behavior, refund patterns, or other fraud-related signals.

## Technology Stack

### Frontend

* Next.js
* TypeScript
* Tailwind CSS
* Supabase client integration
* API wrapper structure for frontend-backend communication

### Backend

* FastAPI
* Python
* Supabase / PostgreSQL
* Pydantic
* REST API design
* Rule-based risk scoring
* RAG-style chatbot support

### AI / Retrieval Components

* TF-IDF retrieval
* BM25 / hybrid ranking
* FAQ and policy document retrieval
* Intent classification
* Bilingual support
* Optional vector database dependencies for future extension

### Database / Infrastructure

* Supabase PostgreSQL
* Supabase project environment variables
* Render / Vercel deployment used in the live prototype environment, but not directly controlled by this repository

## Repository Structure

```text
BackstagePassPrototypeCode/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── config/
│   │   ├── core/
│   │   ├── db/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── main.py
│   │   ├── rag_core.py
│   │   └── temporary_auth.py
│   ├── data/
│   ├── eval/
│   ├── migration_reference/
│   ├── sql/
│   ├── tests/
│   ├── ui_demo/
│   ├── vectordb/
│   ├── .env.example
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── docs/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   ├── .env.example
│   ├── package.json
│   ├── next.config.mjs
│   ├── tsconfig.json
│   └── README.md
│
├── docs/
│   ├── 00_PROJECT_OVERVIEW.txt
│   ├── 01_API_CONTRACT.txt
│   ├── 02_DB_SCHEMA.txt
│   ├── 03_UI_MAPPING.txt
│   ├── 04_DEMO_SCRIPT.txt
│   ├── 05_CURRENT_STATUS.txt
│   └── 06_ARCHITECTURE.txt
│
├── .gitignore
├── package.json
└── README.md
```

## Documentation

The `docs/` folder contains project-level documentation for academic review:

* `00_PROJECT_OVERVIEW.txt` — project goal, MVP flow, key features, and technology stack
* `01_API_CONTRACT.txt` — API contract and endpoint design
* `02_DB_SCHEMA.txt` — database schema notes
* `03_UI_MAPPING.txt` — mapping between UI pages and backend/API functions
* `04_DEMO_SCRIPT.txt` — demonstration flow
* `05_CURRENT_STATUS.txt` — current implementation status
* `06_ARCHITECTURE.txt` — system architecture and component relationship

## Backend Setup

Navigate to the backend folder:

```bash
cd backend
```

Create and activate a Python virtual environment:

```bash
python -m venv .venv
```

For Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

For Windows Command Prompt:

```bash
.venv\Scripts\activate
```

For macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the backend environment file:

```bash
copy .env.example .env
```

On macOS/Linux:

```bash
cp .env.example .env
```

Then fill in the required Supabase environment variables.

Run the backend locally:

```bash
uvicorn app.main:app --reload
```

The local API documentation should then be available at:

```text
http://127.0.0.1:8000/docs
```

## Frontend Setup

Navigate to the frontend folder:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create the frontend environment file:

```bash
copy .env.example .env.local
```

On macOS/Linux:

```bash
cp .env.example .env.local
```

Fill in the required frontend environment variables.

Run the frontend locally:

```bash
npm run dev
```

The frontend should then be available at:

```text
http://localhost:3000
```

## Environment Variables

Environment variables are intentionally excluded from this repository.

Example files are provided:

```text
backend/.env.example
frontend/.env.example
```

The actual `.env` and `.env.local` files should not be committed.

### Backend Example

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_ANON_KEY=
```

### Frontend Example

```env
NEXT_PUBLIC_API_BASE_URL=
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

## Main Backend Modules

The backend prototype includes modules for:

* Event APIs
* Order and booking flow
* Ticket wallet and QR check-in
* Chat and fan engagement
* Rewards
* Artist following
* Notifications
* User profiles
* AI chatbot / RAG retrieval
* Risk scoring / fraud detection
* Supabase integration

## Main Frontend Modules

The frontend prototype includes page and component structures for:

* Login and protected routes
* Dashboard
* Event discovery
* Event details
* Ticket purchase flow
* Ticket wallet
* QR ticket display
* Chat interface
* Rewards
* Artist following
* Notifications
* User profile-related pages

## Stress Test Results

Stress test results are stored in a separate repository:

```text
https://github.com/NagitoKarahashi/BackstagePassStresstest
```

The stress test repository should include:

* Test objective
* Test environment
* Tested endpoints
* Test configuration
* Response time results
* Failure rate
* Screenshots
* Raw or processed result data

## Security Notes

This repository does not include:

* Real `.env` files
* API keys
* Supabase service role keys
* Privy secrets
* Database passwords
* Access tokens
* Production deployment credentials
* Real user data

Only `.env.example` files are included to show the required configuration format.

## Project Status

This repository represents the prototype code and supporting documentation for the Backstage Pass graduation project.

The main implemented or demonstrated areas include:

* Event discovery
* Ticket ordering
* Digital ticket wallet
* QR check-in
* AI chatbot support
* Fan engagement features
* Basic reward system
* Risk / fraud scoring prototype
* Supabase-backed data structure
* Frontend-backend API alignment

## Notes for Reviewers

This repository is intended for code inspection and academic evaluation. Some features are implemented as prototype, mock, or demonstration-level modules rather than production-ready commercial services.

The active deployment may use a separate repository or deployment configuration. This repository is mainly used to present the project structure, implementation logic, API design, and documentation clearly.

## Author

Tan Zhi

Dissertation Project: Backstage Pass — AI + Web3-inspired Event Ticketing and Fan Engagement Platform
