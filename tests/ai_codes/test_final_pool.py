import asyncio
import sys
import logging
sys.path.insert(0, 'D:/codes/nb_libs')
from nb_libs.temps.aiopool3 import SmartAsyncPool, smart_run

logging.basicConfig(level=logging.INFO)

async def task(x):
    await asyncio.sleep(0.05)
    return x * 2

async def test_new_features():
    print("="*60)
    print("测试新增功能")
    print("="*60)
    
    pool = SmartAsyncPool(max_concurrency=10, min_workers=2, auto_shutdown=True)
    
    # 提交一些任务
    for i in range(5):
        await pool.submit(task, i)
    
    # 测试新增的属性
    print(f"\n📊 Pool状态:")
    print(f"  - Worker数量: {pool.worker_count}")
    print(f"  - 繁忙Worker: {pool.busy_worker_count}")
    print(f"  - 空闲Worker: {pool.idle_worker_count}")
    print(f"  - Pending任务: {pool.pending_count}")
    print(f"  - Pool repr: {repr(pool)}")
    
    # 等待一会
    await asyncio.sleep(0.1)
    
    # 再次检查
    print(f"\n📊 0.1秒后:")
    print(f"  - Pending任务: {pool.pending_count}")
    print(f"  - {repr(pool)}")
    
    # 测试cancel_all
    for i in range(10, 20):
        await pool.submit(task, i)
    
    print(f"\n📊 提交10个新任务后:")
    print(f"  - Pending任务: {pool.pending_count}")
    
    cancelled = await pool.cancel_all()
    print(f"\n🚫 取消了 {cancelled} 个任务")
    print(f"  - Pending任务: {pool.pending_count}")
    
    # 重新提交并正常完成
    for i in range(3):
        await pool.submit(task, i)
    
    print(f"\n📊 重新提交3个任务")
    print(f"  - {repr(pool)}")

smart_run(test_new_features())

