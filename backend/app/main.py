from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.config import get_settings
from app.routers import (
    events,
    bookings,
    tickets,
    chat,
    rewards,
    artists,
    orders,
    checkin,
    fraud,
    profiles,
    me,
    notifications,
    ask,
    risk,
    marketplace,
    support_enquiry,
    wallet, 
    web3, 
    marketplace,
)

settings = get_settings()
app = FastAPI(title=settings.app_name)

raw_origins = os.getenv("CORS_ORIGINS", "")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

if not allowed_origins:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://backstage-pass-code-by-tan-65w6.vercel.app",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}

app.include_router(orders.router, prefix=settings.api_prefix)
app.include_router(checkin.router, prefix=settings.api_prefix)
app.include_router(fraud.router, prefix=settings.api_prefix)
app.include_router(events.router, prefix=settings.api_prefix)
app.include_router(bookings.router, prefix=settings.api_prefix)
app.include_router(tickets.router, prefix=settings.api_prefix)
app.include_router(chat.router, prefix=settings.api_prefix)
app.include_router(rewards.router, prefix=settings.api_prefix)
app.include_router(artists.router, prefix=settings.api_prefix)
app.include_router(profiles.router, prefix=settings.api_prefix)
app.include_router(me.router, prefix=settings.api_prefix)
app.include_router(notifications.router, prefix=settings.api_prefix)
app.include_router(ask.router, prefix=settings.api_prefix)
app.include_router(risk.router, prefix=settings.api_prefix)
app.include_router(marketplace.router, prefix=settings.api_prefix)
app.include_router(support_enquiry.router, prefix=settings.api_prefix)
app.include_router(wallet.router, prefix="/api/v1")
app.include_router(web3.router, prefix="/api/v1")
app.include_router(marketplace.router, prefix="/api/v1")