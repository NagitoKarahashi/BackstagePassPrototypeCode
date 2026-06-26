<<<<<<< HEAD
# BackstagePassPrototypeCode
=======
# Backstage Pass

All coded by Tan Zhi
Backstage Pass is an AI + Web3-inspired event ticketing and fan engagement system.
This repository is the Backstage Pass project's prototype codes resources. Illustration Only, Not used in vercel or render.

## Project Structure

- `ai-service/` - FastAPI backend service
- `backstage-pass-frontend-starter/` - Next.js frontend
- `docs/` - project documents

## Tech Stack

### Frontend
- Next.js
- Tailwind CSS

### Backend
- FastAPI
- Supabase
- Python

## Requirements

- Git
- Node.js 18+
- npm
- Python 3.10+
- Supabase project

## Environment Variables

### Frontend
Create:
`backstage-pass-frontend-starter/.env.local`

based on:
`backstage-pass-frontend-starter/.env.example`

### Backend
Create:
`ai-service/.env`

based on:
`ai-service/.env.example`

## Frontend Setup

```bash
cd backstage-pass-frontend-starter
npm install
npm run dev

http://127.0.0.1:8000/docs

## Backend Setup

cd ai-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

http://localhost:3000

# Notes

Do not commit .env, node_modules, .next, or virtual environments.
Make sure the backend is running before testing frontend API calls.
Update environment variables before local deployment.
>>>>>>> cc1d8cc (Initial project upload)
