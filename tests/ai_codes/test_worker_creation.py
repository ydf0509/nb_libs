import asyncio
import sys
sys.path.insert(0, 'D:/codes/nb_libs')
from nb_libs.temps.aiopool3 import SmartAsyncPool

async def fast_task(x: int):
    """很快完成的任务"""
    await asyncio.sleep(0.01)  # 只需要0.01秒
    print(f"Task {x} done by worker {id(asyncio.current_task())}")
    return x

async def test_fast_consumption():
    """测试：worker消费很快的场景"""
    print("=" * 50)
    print("测试场景：100个并发上限，快速submit 90个快速任务")
    print("=" * 50)
    
    async with SmartAsyncPool(max_concurrency=100, max_queue_size=1000, min_workers=0) as pool:
        # 快速提交90个任务
        futures = []
        for i in range(90):
            fut = await pool.submit(fast_task, i)
            futures.append(fut)
            if i % 10 == 0:
                print(f"Submitted {i} tasks, current workers: {len(pool._workers)}, queue: {pool._queue.qsize()}")
        
        print(f"\n提交完成！")
        print(f"最终创建的worker数量: {len(pool._workers)}")
        print(f"当前队列大小: {pool._queue.qsize()}")
        
        # 等待所有任务完成
        results = await asyncio.gather(*futures)
        print(f"\n所有任务完成，共处理 {len(results)} 个任务")

if __name__ == "__main__":
    asyncio.run(test_fast_consumption())

