from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.currency_trade_volume_service import CurrencyPair


class HistoryItem(BaseModel):
    time: datetime
    volume: float

    # orm_mode allows dataclasses to pass this validation, otherwise we would have to convert them to dicts first
    # See https://pydantic-docs.helpmanual.io/usage/model_config/
    class Config:
        orm_mode = True


class HistoryApiResponse(BaseModel):
    currency_pair: CurrencyPair
    history: List[HistoryItem]
    rank: int
    total_tracked_currency_pairs: int

    # orm_mode allows dataclasses to pass this validation, otherwise we would have to convert them to dicts first
    # See https://pydantic-docs.helpmanual.io/usage/model_config/
    class Config:
        orm_mode = True


class RecordTradeVolumeResponse(BaseModel):
    success: bool
