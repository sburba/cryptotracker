import asyncio
from mock import MagicMock

import pytest
from app.currency_trade_volume_service import (
    CurrencyTradeVolumeService,
    PairNotFoundException,
    CurrencyPair,
    CurrencyPairSnapshot,
)
from app.currency_trade_volume_store import (
    CurrencyTradeVolumeStore,
    CurrencyPairAvg,
    CurrencyPairRank,
)
from app.livecoin_api import LivecoinApi
from app.mailer import Mailer
from app.types import CurrencyTradeVolumeRecord
from datetime import datetime

JAN_1ST = datetime(year=1970, day=1, month=1)

mock_store = MagicMock(CurrencyTradeVolumeStore)
mock_api = MagicMock(LivecoinApi)
mock_mailer = MagicMock(Mailer)

NOTIFY_EMAILS = ["example@local"]


def async_return(result):
    f = asyncio.Future()
    f.set_result(result)
    return f


@pytest.fixture
async def service():
    yield CurrencyTradeVolumeService(
        store=mock_store, api=mock_api, mailer=mock_mailer, notify_emails=NOTIFY_EMAILS
    )
    mock_store.reset_mock()
    mock_api.reset_mock()
    mock_mailer.reset_mock()


@pytest.mark.asyncio
async def test_alert_on_trade_volume_spike(service: CurrencyTradeVolumeService):
    """
    Verify that if the current trading
    """
    mock_api.fetch_trade_volumes.return_value = [
        CurrencyTradeVolumeRecord(
            time=JAN_1ST, currency_pair="currency_pair", volume=300
        )
    ]

    mock_store.get_currency_pair_averages.return_value = [
        CurrencyPairAvg("currency_pair", avg_volume=100)
    ]

    await service.update_trade_volumes()

    mock_mailer.send_mail.assert_called_once_with(
        NOTIFY_EMAILS[0], "CryptoTracker Alert", "currency_pair is trading at 300"
    )


@pytest.mark.asyncio
async def test_no_alert_on_normal_trade_volume(service: CurrencyTradeVolumeService):
    mock_api.fetch_trade_volumes.return_value = [
        CurrencyTradeVolumeRecord(
            time=JAN_1ST, currency_pair="currency_pair", volume=150
        )
    ]

    mock_store.get_currency_pair_averages.return_value = [
        CurrencyPairAvg("currency_pair", avg_volume=100)
    ]

    await service.update_trade_volumes()

    mock_mailer.send_mail.assert_not_called()


@pytest.mark.asyncio
async def test_no_alert_on_zero_trade_volume(service: CurrencyTradeVolumeService):
    mock_api.fetch_trade_volumes.return_value = [
        CurrencyTradeVolumeRecord(time=JAN_1ST, currency_pair="currency_pair", volume=0)
    ]

    mock_store.get_currency_pair_averages.return_value = [
        CurrencyPairAvg("currency_pair", avg_volume=0)
    ]

    await service.update_trade_volumes()

    mock_mailer.send_mail.assert_not_called()


@pytest.mark.asyncio
async def test_snapshot_missing_rank(service: CurrencyTradeVolumeService):
    mock_store.get_currency_pair_ranks.return_value = []
    mock_store.get_currency_pair_history.return_value = []

    with pytest.raises(PairNotFoundException):
        await service.get_currency_pair_snapshot(CurrencyPair.DGB_TO_BTC)


@pytest.mark.asyncio
async def test_get_snapshot_valid_rank(service: CurrencyTradeVolumeService):
    mock_store.get_currency_pair_ranks.return_value = [
        CurrencyPairRank(
            rank=1, currency_pair=CurrencyPair.DGB_TO_BTC, volume_std_dev=300
        ),
        CurrencyPairRank(
            rank=2, currency_pair=CurrencyPair.OTON_TO_BTC, volume_std_dev=100
        ),
    ]

    history = [
        CurrencyTradeVolumeRecord(
            currency_pair=CurrencyPair.DGB_TO_BTC, time=JAN_1ST, volume=200
        )
    ]
    mock_store.get_currency_pair_history.return_value = history
    snapshot = await service.get_currency_pair_snapshot(CurrencyPair.DGB_TO_BTC)

    assert snapshot == CurrencyPairSnapshot(CurrencyPair.DGB_TO_BTC, history, 1, 3)
