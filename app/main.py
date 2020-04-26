import logging
import sys

import httpx
import uvicorn
from fastapi import FastAPI

from app import settings
from app.currency_trade_volume_service import CurrencyPair
from app.di import make_deps
from app.response_types import HistoryApiResponse, RecordTradeVolumeResponse

app = FastAPI()

# We're going to close the client manually in the shutdown event
client = httpx.AsyncClient()
deps = make_deps(client)
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)


@app.on_event("startup")
async def startup():
    await deps.database.connect()


@app.on_event("shutdown")
async def shutdown():
    await deps.database.disconnect()
    await client.aclose()


@app.get("/api/volume_history", response_model=HistoryApiResponse)
async def volume_history(currency_pair: CurrencyPair):
    return await deps.currency_trade_service.get_currency_pair_snapshot(currency_pair)


@app.get("/webhook/record_trade_volume")
async def record_trade_volume() -> RecordTradeVolumeResponse:
    await deps.currency_trade_service.update_trade_volumes()

    return RecordTradeVolumeResponse(success=True)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
