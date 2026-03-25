"""
测试10万任务的内存泄漏和性能
"""
import asyncio
import time
import psutil
import os
import sys
sys.path.insert(0, 'nb_libs/temps')

from aiopool3 import SmartAsyncPool

# 获取当前进程
process = psutil.Process(os.getpid())

async def small_task(x: int):
    """简单的任务，避免任务本身占用太多资源"""
    # await asyncio.sleep(0.001)  # 1ms
    if x%20000 == 0:
        print(f"正在执行任务: {x}")
    return x * 2

async def test_100k_tasks():
    """测试10万任务"""
    print("="*60)
    print("测试：提交10万任务，检查内存和性能")
    print("="*60)
    
    # 记录初始内存
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    print(f"初始内存: {initial_memory:.2f} MB")
    
    pool = SmartAsyncPool(max_concurrency=1000, min_workers=10, auto_shutdown=True)
    
    # 提交10万任务
    print("\n开始提交10万任务...")
    start_time = time.time()
    
    futures = []
    for i in range(1000000):
        future = await pool.submit(small_task, i)
        # futures.append(future)
        
        # 每1万个任务报告一次
        if (i + 1) % 10000 == 0:
            current_memory = process.memory_info().rss / 1024 / 1024
            elapsed = time.time() - start_time
            print(f"  已提交 {i+1:,} 个任务 | "
                  f"内存: {current_memory:.2f} MB (+{current_memory - initial_memory:.2f}) | "
                  f"速度: {(i+1)/elapsed:.0f} tasks/s | "
                  f"pending: {pool.pending_count}")
    
    submit_time = time.time() - start_time
    print(f"\n✅ 提交完成！耗时: {submit_time:.2f}秒，速度: {100000/submit_time:.0f} tasks/s")
    
    # 检查内存
    after_submit_memory = process.memory_info().rss / 1024 / 1024
    print(f"提交后内存: {after_submit_memory:.2f} MB (+{after_submit_memory - initial_memory:.2f})")
    
    # 等待所有任务完成
    print("\n等待所有任务完成...")
    wait_start = time.time()
    await asyncio.gather(*futures)
    wait_time = time.time() - wait_start
    print(f"✅ 所有任务完成！耗时: {wait_time:.2f}秒")
    
    # 检查完成后的内存
    after_complete_memory = process.memory_info().rss / 1024 / 1024
    print(f"完成后内存: {after_complete_memory:.2f} MB (+{after_complete_memory - initial_memory:.2f})")
    print(f"pending count: {pool.pending_count}")
    
    # 关闭pool
    await pool.shutdown(wait=True)
    
    # 最终内存
    final_memory = process.memory_info().rss / 1024 / 1024
    print(f"关闭后内存: {final_memory:.2f} MB (+{final_memory - initial_memory:.2f})")
    
    # 分析
    print("\n" + "="*60)
    print("内存分析")
    print("="*60)
    memory_increase = final_memory - initial_memory
    print(f"总内存增长: {memory_increase:.2f} MB")
    print(f"平均每任务: {memory_increase * 1024 / 100000:.2f} KB")
    
    if memory_increase < 100:  # 小于100MB
        print("✅ 内存控制良好！")
    elif memory_increase < 500:
        print("⚠️  内存占用较高，但可接受")
    else:
        print("❌ 可能存在内存泄漏！")
    
    print("\n性能分析")
    print("="*60)
    total_time = submit_time + wait_time
    throughput = 100000 / total_time
    print(f"总耗时: {total_time:.2f}秒")
    print(f"吞吐量: {throughput:.0f} tasks/s")
    
    if throughput > 10000:
        print("✅ 性能优秀！")
    elif throughput > 5000:
        print("✅ 性能良好")
    elif throughput > 1000:
        print("⚠️  性能一般")
    else:
        print("❌ 性能较差")

if __name__ == "__main__":
    asyncio.run(test_100k_tasks())

