import sys
from datetime import datetime
from typing import List
import logging

import httpx
import uvicorn
from databases import Database
from fastapi import FastAPI
from pydantic import BaseModel
from sendgrid import SendGridAPIClient

from app import settings
from app.currency_trade_volume_service import CurrencyTradeVolumeService, CurrencyPair
from app.currency_trade_volume_store import CurrencyTradeVolumeStore
from app.livecoin_api import LivecoinApi
from app.mailer import SendGridMailer, LoggingMailer

app = FastAPI()

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

database = Database(settings.DATABASE_URL)
if settings.USE_REAL_MAILER:
    mailer = SendGridMailer(SendGridAPIClient(settings.SENDGRID_API_KEY))
else:
    mailer = LoggingMailer(logging.getLogger("Mail"))


class HistoryItem(BaseModel):
    time: datetime
    volume: float

    class Config:
        orm_mode = True


class HistoryApiResponse(BaseModel):
    currency_pair: CurrencyPair
    history: List[HistoryItem]
    rank: int
    total_tracked_currency_pairs: int

    class Config:
        orm_mode = True


class RecordTradeVolumeResponse(BaseModel):
    success: bool


def make_service(client: httpx.AsyncClient):
    return CurrencyTradeVolumeService(
        store=CurrencyTradeVolumeStore(database),
        api=LivecoinApi(client),
        mailer=mailer,
        notify_emails=settings.NOTIFY_EMAILS,
    )


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/api/volume_history", response_model=HistoryApiResponse)
async def volume_history(currency_pair: CurrencyPair):
    # TODO: FastAPI has a real dependency injection system, we should use that
    async with httpx.AsyncClient() as client:
        service = make_service(client)
        return await service.get_currency_pair_snapshot(currency_pair)


@app.get("/webhook/record_trade_volume")
async def record_trade_volume() -> RecordTradeVolumeResponse:
    # TODO: FastAPI has a real dependency injection system, we should use that
    async with httpx.AsyncClient() as client:
        service = make_service(client)
        await service.update_trade_volumes()

    return RecordTradeVolumeResponse(success=True)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
