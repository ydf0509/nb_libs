# client.py
import aiohttp
import asyncio

session = aiohttp.ClientSession()


async def fetch():

        async with session.get('https://httpbin.org/get') as response:
            print("Status:", response.status)
            data = await response.json()
            print("Response JSON keys:", list(data.keys()))

# Python ≥3.7
asyncio.run(fetch())