from datetime import datetime, timezone
from typing import List

import httpx
from pydantic import BaseModel

from app.types import CurrencyTradeVolumeRecord


class ApiUnavailableException(Exception):
    pass


class TickerItem(BaseModel):
    symbol: str
    volume: int


class TickerApiResponse(BaseModel):
    __root__: List[TickerItem]


class LivecoinApi:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def fetch_trade_volumes(
        self, currency_pairs: List[str],
    ) -> List[CurrencyTradeVolumeRecord]:
        # TODO: Log details about the request/response
        bare_resp = await self._client.get("https://api.livecoin.net/exchange/ticker")

        if bare_resp.status_code != 200:
            # TODO: log details about the error, maybe not needed if the
            # request/response logging is good
            raise ApiUnavailableException()

        fetch_time = datetime.now(timezone.utc)
        ticker_items = TickerApiResponse.parse_obj(bare_resp.json()).__root__

        trade_volume_records: List[CurrencyTradeVolumeRecord] = []
        for item in ticker_items:
            if item.symbol in currency_pairs:
                trade_volume_records.append(
                    CurrencyTradeVolumeRecord(
                        time=fetch_time, currency_pair=item.symbol, volume=item.volume
                    ),
                )

        return trade_volume_records
