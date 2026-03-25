import asyncio
import time


async def hello():
    while True:
        print("async alive")
        await asyncio.sleep(1)

loop = asyncio.get_event_loop()
loop.create_task(hello())

# 错误！
while True:
    time.sleep(100)
