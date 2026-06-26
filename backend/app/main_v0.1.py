from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.ask import router as ask_router
from app.api.chat import router as chat_router
from app.api.fraud import router as fraud_router
from app.api.events import router as events_router
from app.api.tickets import router as tickets_router
from app.api.me import router as me_router
from app.api.bookings import router as bookings_router
from app.api.checkin import router as checkin_router
from app.api.wallet import router as wallet_router

app = FastAPI(title="Backstage Pass Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(ask_router, prefix="/api/v1", tags=["ai"])
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
app.include_router(fraud_router, prefix="/api/v1", tags=["fraud"])
app.include_router(bookings_router, prefix="/api/v1", tags=["bookings"])
app.include_router(checkin_router, prefix="/api/v1", tags=["checkin"])
app.include_router(wallet_router, prefix="/api/v1", tags=["wallet"])