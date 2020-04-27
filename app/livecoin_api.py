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
        # TODO: Handle rate-limit responses by backing-off instead of just failing
        bare_resp = await self._client.get("https://api.livecoin.net/exchange/ticker")

        if bare_resp.status_code != 200:
            # TODO: log details about the error, maybe not needed if the
            # request/response logging is good
            raise ApiUnavailableException()

        fetch_time = datetime.now(timezone.utc)
        ticker_items = TickerApiResponse.parse_obj(bare_resp.json()).__root__

        trade_volume_records: List[CurrencyTradeVolumeRecord] = []
        for item in ticker_items:
            # It's unfortunate that we request all metrics from livecoin and then filter after we receive them. The API
            # does allow requesting a single currency pair so we could request ones we care about in parallel, but
            # there's a 1 request/second API limit so instead we just load all of them
            if item.symbol in currency_pairs:
                trade_volume_records.append(
                    CurrencyTradeVolumeRecord(
                        time=fetch_time, currency_pair=item.symbol, volume=item.volume
                    ),
                )

        return trade_volume_records
