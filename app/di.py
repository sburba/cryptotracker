import logging
from dataclasses import dataclass

import httpx
from databases import Database
from sendgrid import SendGridAPIClient

from app import settings
from app.currency_trade_volume_service import CurrencyTradeVolumeService
from app.currency_trade_volume_store import CurrencyTradeVolumeStore
from app.livecoin_api import LivecoinApi
from app.mailer import SendGridMailer, LoggingMailer


# TODO: FastAPI has a real dependency injection system, we should use that
@dataclass
class Deps:
    currency_trade_service: CurrencyTradeVolumeService
    database: Database


def make_deps(client: httpx.AsyncClient) -> Deps:
    database = Database(settings.DATABASE_URL)

    if settings.USE_REAL_MAILER:
        mailer = SendGridMailer(SendGridAPIClient(settings.SENDGRID_API_KEY))
    else:
        mailer = LoggingMailer(logging.getLogger("Mail"))

    service = CurrencyTradeVolumeService(
        store=CurrencyTradeVolumeStore(database),
        api=LivecoinApi(client),
        mailer=mailer,
        notify_emails=settings.NOTIFY_EMAILS,
    )

    return Deps(service, database)
