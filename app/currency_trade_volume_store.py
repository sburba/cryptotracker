from dataclasses import dataclass
from typing import List

from databases import Database

from app.types import CurrencyTradeVolumeRecord


@dataclass
class CurrencyPairRank:
    rank: int
    currency_pair: str
    volume_std_dev: float


@dataclass
class CurrencyPairAvg:
    currency_pair: str
    avg_volume: float


class CurrencyTradeVolumeStore:
    def __init__(self, db: Database):
        self._db = db

    async def record_trade_volumes(self, records: List[CurrencyTradeVolumeRecord]):
        """
        Store the given trade volumes
        """

        query = """
        INSERT INTO currency_pair_volumes(fetch_time, volume, currency_pair)
        VALUES (:fetch_time, :volume, :currency_pair)
        """
        values = [
            {
                "fetch_time": record.time,
                "volume": record.volume,
                "currency_pair": record.currency_pair,
            }
            for record in records
        ]
        # TODO: Use a real bulk insert here
        # This will perform a seperate insert for each value. Since we only track
        # three currency pairs and update once a minute right now it doesn't really
        # matter for performance but it will matter as we scale to tracking more
        # currency pairs. Once we do bulk insert, we will want to make sure we're
        # batching the inserts as necessary to keep under the max query size.
        await self._db.execute_many(query=query, values=values)

    async def get_currency_pair_averages(self) -> List[CurrencyPairAvg]:
        """
        Fetch the trade volume average for all currency pairs over the last hour
        """

        query = """
            SELECT currency_pair, avg(volume) as avg_volume
            FROM currency_pair_volumes
            WHERE fetch_time >= NOW() - INTERVAL '1 HOUR'
            GROUP BY currency_pair
        """

        rows = await self._db.fetch_all(query)
        return [
            CurrencyPairAvg(
                currency_pair=row["currency_pair"], avg_volume=row["avg_volume"]
            )
            for row in rows
        ]

    async def get_currency_pair_ranks(self) -> List[CurrencyPairRank]:
        """
        Fetch a list of currency pair volume standard deviations over the last 24 hours
        """

        query = """
            SELECT currency_pair, stddev(volume) as volume_std_dev
            FROM currency_pair_volumes
            WHERE fetch_time >= NOW() - INTERVAL '24 HOURS'
            GROUP BY currency_pair
            ORDER BY
                volume_std_dev DESC,
                -- Sort by currency pair as well so that results are consistent even when the
                -- volume standard deviations are the same
                currency_pair DESC
        """

        rows = await self._db.fetch_all(query)
        # Query sorts by std_dev, so they are in rank order, but have to add one since ranks aren't zero-indexed
        return [
            CurrencyPairRank(
                rank=index + 1,
                currency_pair=row["currency_pair"],
                volume_std_dev=row["volume_std_dev"],
            )
            for index, row in enumerate(rows)
        ]

    async def get_currency_pair_history(
        self, currency_pair: str,
    ) -> List[CurrencyTradeVolumeRecord]:
        """
        Fetch all of the trade volumes for the past 24 hours for the given currency pair
        """
        query = """
            SELECT currency_pair, fetch_time, volume
            FROM currency_pair_volumes
            WHERE fetch_time >= NOW() - INTERVAL '24 hours'
            AND currency_pair = :currency_pair
        """

        rows = await self._db.fetch_all(query, {"currency_pair": currency_pair})

        return [
            CurrencyTradeVolumeRecord(
                row["fetch_time"], row["currency_pair"], row["volume"]
            )
            for row in rows
        ]
