import asyncio
import sys
import logging
sys.path.insert(0, 'D:/codes/nb_libs')
from nb_libs.temps.aiopool3 import SmartAsyncPool, wait_for_all_pools_done, shutdown_all_pools

logging.basicConfig(level=logging.INFO)

async def task(x):
    await asyncio.sleep(0.1)
    print(f"Task {x} done")
    return x * 2

async def test_wait_then_shutdown():
    print("="*50)
    print("测试：先wait_for_all_pools_done，再shutdown_all_pools")
    print("="*50)
    
    pool = SmartAsyncPool(max_concurrency=10, min_workers=0, auto_shutdown=True)
    
    # 提交任务
    await pool.submit(task, 1)
    await pool.submit(task, 2)
    
    print(f"📊 提交了2个任务，pending: {pool.pending_count}")
    
    # 先wait
    print("\n1️⃣  调用 wait_for_all_pools_done...")
    await wait_for_all_pools_done()
    print(f"✅ wait完成，pending: {pool.pending_count}")
    
    # 再shutdown
    print("\n2️⃣  调用 shutdown_all_pools...")
    try:
        await shutdown_all_pools()
        print("✅ shutdown成功")
    except Exception as e:
        print(f"❌ shutdown失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_wait_then_shutdown())

