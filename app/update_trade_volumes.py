#!/usr/bin/python3
import asyncio
import logging
import sys

import httpx

from app.di import make_deps


async def main():
    async with httpx.AsyncClient() as client:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
        deps = make_deps(client)
        await deps.database.connect()
        await deps.currency_trade_service.update_trade_volumes()
        await deps.database.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
