import asyncio
import sys
sys.path.insert(0, 'D:/codes/nb_libs')
from nb_libs.temps.aiopool3 import SmartAsyncPool

async def instant_task(x: int):
    """几乎瞬间完成的任务"""
    # 不sleep，立即返回
    return x * 2

async def test_extreme_fast():
    """极端场景：任务几乎瞬间完成"""
    print("=" * 50)
    print("极端测试：worker几乎瞬间消费任务")
    print("=" * 50)
    
    async with SmartAsyncPool(max_concurrency=100, max_queue_size=1000, min_workers=0) as pool:
        # 快速提交90个瞬间完成的任务
        futures = []
        for i in range(90):
            fut = await pool.submit(instant_task, i)
            futures.append(fut)
            # 每10个打印一次状态
            if i % 10 == 9:
                busy = sum(1 for b in pool._worker_busy.values() if b)
                idle = len(pool._workers) - busy
                print(f"已提交 {i+1} 个任务 | workers={len(pool._workers)} | busy={busy} | idle={idle} | queue={pool._queue.qsize()}")
        
        print(f"\n提交完成！")
        print(f"最终worker数量: {len(pool._workers)}")
        busy = sum(1 for b in pool._worker_busy.values() if b)
        print(f"繁忙worker: {busy}")
        print(f"空闲worker: {len(pool._workers) - busy}")
        print(f"队列大小: {pool._queue.qsize()}")
        
        # 等待所有任务完成
        results = await asyncio.gather(*futures)
        print(f"\n任务完成，共处理 {len(results)} 个")

if __name__ == "__main__":
    asyncio.run(test_extreme_fast())

