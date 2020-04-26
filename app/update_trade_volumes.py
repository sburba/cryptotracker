#!/usr/bin/python3
import asyncio

import httpx

from app.di import make_deps


async def main():
    async with httpx.AsyncClient() as client:
        deps = make_deps(client)
        await deps.database.connect()
        await deps.currency_trade_service.update_trade_volumes()
        await deps.database.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
