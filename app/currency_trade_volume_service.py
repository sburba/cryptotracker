from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from app.currency_trade_volume_store import CurrencyTradeVolumeStore, CurrencyPairAvg
from app.livecoin_api import LivecoinApi
from app.mailer import Mailer
from app.types import CurrencyTradeVolumeRecord


# Free heroku database can only hold 10,000 rows so just store a couple of them
# as an example. These were picked by looking for ones that have a larger
# variance in short time scales
class CurrencyPair(str, Enum):
    XEM_TO_BTC = "XEM/BTC"
    OTON_TO_BTC = "OTON/BTC"
    DGB_TO_BTC = "DGB/BTC"


_TRACKED_PAIRS = [pair.value for pair in CurrencyPair]


class PairNotFoundException(Exception):
    pass


@dataclass
class CurrencyPairSnapshot:
    currency_pair: str
    history: List[CurrencyTradeVolumeRecord]
    rank: int
    """
    The currency pair's position in the list of all tracked currency pairs
    sorted by the standard deviation of their trade volume over the last 24
    hours
    """
    total_tracked_currency_pairs: int


def _find_avg_volume(
    currency_pair: str, avg_trade_volumes: List[CurrencyPairAvg]
) -> Optional[float]:
    for avg_volume_record in avg_trade_volumes:
        if avg_volume_record.currency_pair == currency_pair:
            return avg_volume_record.avg_volume

    return None


def _is_notable_volume_change(new_trade_volume: float, avg_trade_volume: float) -> bool:
    return avg_trade_volume > 0 and new_trade_volume >= avg_trade_volume * 3


class CurrencyTradeVolumeService:
    def __init__(
        self,
        store: CurrencyTradeVolumeStore,
        api: LivecoinApi,
        mailer: Mailer,
        notify_emails: List[str],
    ):
        self._store = store
        self._api = api
        self._mailer = mailer
        self._notify_emails = notify_emails

    async def update_trade_volumes(self):
        """
        Load another batch of trade volumes from the API and record them
        Send out email alerts for notable changes in trade volume
        """

        trade_volumes = await self._api.fetch_trade_volumes(_TRACKED_PAIRS)
        await self._store.record_trade_volumes(trade_volumes)
        avg_trade_volumes = await self._store.get_currency_pair_averages()

        # We could likely trade memory usage for speed if there are huge numbers of tracked currency pairs here by first
        # creating a hash map of average trade volumes indexed by currency pair instead of searching for them in the
        # list every time
        for trade_volume in trade_volumes:
            avg_volume = _find_avg_volume(trade_volume.currency_pair, avg_trade_volumes)
            if avg_volume is not None and _is_notable_volume_change(
                trade_volume.volume, avg_volume
            ):
                for email in self._notify_emails:
                    self._mailer.send_mail(
                        email,
                        "CryptoTracker Alert",
                        f"{trade_volume.currency_pair} is trading at {trade_volume.volume}",
                    )

    async def get_currency_pair_snapshot(
        self, currency_pair: CurrencyPair
    ) -> CurrencyPairSnapshot:
        """
        Get a history trade volume history for the last 24 hours of the given currency pair as well as a ranking for the
        amount of fluctuation in the given pair amongst all currency pair trade volumes
        """
        ranks = await self._store.get_currency_pair_ranks()
        history = await self._store.get_currency_pair_history(currency_pair)

        target_rank: Optional[int] = None
        for rank in ranks:
            if rank.currency_pair == currency_pair:
                target_rank = rank.rank

        if target_rank is None:
            # TODO: Log requested currency pair and results
            # This will cause the service to 500 if we have a supported currency pair that we don't have any data for
            # yet (or if the syncing process has failed for the last hour). We should make the API return a custom error
            # code in this case so that the UI can handle that case and display some information
            raise PairNotFoundException()

        return CurrencyPairSnapshot(
            currency_pair, history, target_rank, len(_TRACKED_PAIRS)
        )
