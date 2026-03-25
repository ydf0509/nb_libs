import asyncio
import time
import psutil
import os
import sys
sys.path.insert(0, 'nb_libs/temps')

from aiopool3 import SmartAsyncPool

async def small_task(x: int):
    """简单的任务，避免任务本身占用太多资源"""
    # await asyncio.sleep(0.001)  # 1ms
    if x%20000 == 0:
        print(f"{time.strftime('%H:%M:%S')},正在执行任务: {x}")
    return x * 2

async def test_100k_tasks():
    pool = SmartAsyncPool(max_concurrency=1000, min_workers=10, auto_shutdown=True)
    
    for i in range(1000001):
        await pool.submit(small_task, i)

if __name__ == "__main__":
    asyncio.run(test_100k_tasks())