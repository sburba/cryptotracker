from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.currency_trade_volume_service import CurrencyPair


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

