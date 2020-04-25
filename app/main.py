import uvicorn
from typing import List
from fastapi import FastAPI, HTTPException
from enum import Enum
from pydantic import BaseModel
import datetime

from pydantic.dataclasses import dataclass
import httpx

app = FastAPI()


class TickerItem(BaseModel):
    symbol: str
    volume: int


class TickerApiResponse(BaseModel):
    __root__: List[TickerItem]


class HistoryItem(BaseModel):
    time: datetime.datetime
    value: float


class HistoryApiResponse(BaseModel):
    symbol: str
    history: List[HistoryItem]


class Symbol(str, Enum):
    BNT_TO_BTC = "BNT_BTC"
    GOLD_TO_BTC = "GOLD_BTC"
    CBC_TO_ETH = "CBC_ETH"


@app.get("/api/{symbol}/history", response_model=HistoryApiResponse)
async def history(symbol: Symbol) -> HistoryApiResponse:
    return HistoryApiResponse(
        symbol="BNT/BTC", history=[HistoryItem(time=datetime.datetime.now(), value=1.5)]
    )


@app.get("/webhook/record_metric_stats")
async def record_metric_stats() -> List[TickerItem]:
    async with httpx.AsyncClient() as client:
        bare_resp = await client.get("https://api.livecoin.net/exchange/ticker")

    if bare_resp.status_code != 200:
        # TODO: log
        raise HTTPException(status_code=500)

    ticker_items = TickerApiResponse.parse_obj(bare_resp.json())
    return ticker_items.__root__


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
