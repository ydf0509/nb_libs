import asyncio
import sys
sys.path.insert(0, 'D:/codes/nb_libs')
from nb_libs.temps.aiopool3 import SmartAsyncPool

async def task(x):
    await asyncio.sleep(0.1)
    print(f"Task {x} done")
    return x * 2

async def test_shutdown():
    pool = SmartAsyncPool(max_concurrency=10, min_workers=0, auto_shutdown=True)
    
    # 提交任务
    await pool.submit(task, 1)
    await pool.submit(task, 2)
    
    print(f"Pending: {pool.pending_count}")
    
    # 尝试shutdown
    try:
        await pool.shutdown(wait=True)
        print("✅ Shutdown成功")
    except Exception as e:
        print(f"❌ Shutdown失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_shutdown())

