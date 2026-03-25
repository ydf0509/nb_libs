"""
精确的性能测试
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

async def cpu_task(x: int):
    """纯CPU任务（无IO等待）"""
    result = x * 2
    for _ in range(10):  # 增加一点计算量
        result = result * 1.01
    return result

async def io_task(x: int):
    """模拟IO任务"""
    await asyncio.sleep(0.001)  # 1ms
    return x * 2

async def bench_cpu_tasks(count=100000):
    """测试CPU任务性能"""
    print("="*70)
    print(f"测试1: {count:,} 个CPU任务（无IO等待）")
    print("="*70)
    
    initial_memory = process.memory_info().rss / 1024 / 1024
    print(f"初始内存: {initial_memory:.2f} MB")
    
    pool = SmartAsyncPool(max_concurrency=1000, min_workers=10, auto_shutdown=False)
    
    print(f"\n开始提交 {count:,} 个任务...")
    start_time = time.time()
    
    # 提交任务但不等待（测试提交速度）
    for i in range(count):
        await pool.submit(cpu_task, i)
    
    submit_time = time.time() - start_time
    submit_speed = count / submit_time
    
    print(f"✅ 提交完成！")
    print(f"   耗时: {submit_time:.2f}秒")
    print(f"   速度: {submit_speed:,.0f} tasks/s")
    
    # 等待所有任务完成
    print(f"\n等待任务完成（pending: {pool.pending_count}）...")
    wait_start = time.time()
    await pool.async_wait_for_all()
    wait_time = time.time() - wait_start
    
    print(f"✅ 所有任务完成！")
    print(f"   耗时: {wait_time:.2f}秒")
    print(f"   速度: {count/wait_time:,.0f} tasks/s")
    
    # 总体性能
    total_time = submit_time + wait_time
    total_speed = count / total_time
    
    print(f"\n📊 总体性能:")
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   总吞吐量: {total_speed:,.0f} tasks/s")
    
    final_memory = process.memory_info().rss / 1024 / 1024
    print(f"   内存增长: {final_memory - initial_memory:.2f} MB")
    
    await pool.shutdown(wait=True)
    
    return total_speed

async def bench_io_tasks(count=100000):
    """测试IO任务性能"""
    print("\n" + "="*70)
    print(f"测试2: {count:,} 个IO任务（1ms sleep）")
    print("="*70)
    
    initial_memory = process.memory_info().rss / 1024 / 1024
    print(f"初始内存: {initial_memory:.2f} MB")
    
    pool = SmartAsyncPool(max_concurrency=1000, min_workers=10, auto_shutdown=False)
    
    print(f"\n开始提交 {count:,} 个任务...")
    start_time = time.time()
    
    futures = []
    for i in range(count):
        future = await pool.submit(io_task, i)
        futures.append(future)
    
    submit_time = time.time() - start_time
    
    print(f"✅ 提交完成！耗时: {submit_time:.2f}秒")
    
    # 等待所有任务完成
    print(f"\n等待任务完成...")
    wait_start = time.time()
    await asyncio.gather(*futures)
    wait_time = time.time() - wait_start
    
    print(f"✅ 所有任务完成！")
    print(f"   耗时: {wait_time:.2f}秒")
    
    # 总体性能
    total_time = submit_time + wait_time
    total_speed = count / total_time
    
    print(f"\n📊 总体性能:")
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   总吞吐量: {total_speed:,.0f} tasks/s")
    print(f"   理论最大: {1000 * 1000:,} tasks/s (1000并发 * 1000次/秒)")
    print(f"   实际/理论: {total_speed / 1000000 * 100:.1f}%")
    
    final_memory = process.memory_info().rss / 1024 / 1024
    print(f"   内存增长: {final_memory - initial_memory:.2f} MB")
    
    await pool.shutdown(wait=True)
    
    return total_speed

async def bench_mixed_submit_execute(count=100000):
    """测试边提交边执行的性能"""
    print("\n" + "="*70)
    print(f"测试3: {count:,} 个任务（边提交边执行，不保存future）")
    print("="*70)
    
    pool = SmartAsyncPool(max_concurrency=1000, min_workers=10, auto_shutdown=False)
    
    print(f"\n开始提交+执行 {count:,} 个任务...")
    start_time = time.time()
    
    # 边提交边执行（任务很快完成，不会积压）
    for i in range(count):
        await pool.submit(cpu_task, i)
        
        if (i + 1) % 20000 == 0:
            elapsed = time.time() - start_time
            speed = (i + 1) / elapsed
            print(f"  {i+1:,} tasks | 速度: {speed:,.0f} tasks/s | pending: {pool.pending_count}")
    
    # 等待剩余任务
    if pool.pending_count > 0:
        print(f"\n等待剩余 {pool.pending_count} 个任务...")
        await pool.async_wait_for_all()
    
    total_time = time.time() - start_time
    total_speed = count / total_time
    
    print(f"\n✅ 所有任务完成！")
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   总吞吐量: {total_speed:,.0f} tasks/s")
    
    await pool.shutdown(wait=True)
    
    return total_speed

async def main():
    print("🚀 SmartAsyncPool 性能基准测试\n")
    
    # 测试1：CPU任务
    cpu_speed = await bench_cpu_tasks(100000)
    
    # 测试2：IO任务
    io_speed = await bench_io_tasks(100000)
    
    # 测试3：混合模式
    mixed_speed = await bench_mixed_submit_execute(100000)
    
    # 总结
    print("\n" + "="*70)
    print("📊 性能总结")
    print("="*70)
    print(f"CPU任务吞吐量:     {cpu_speed:>10,.0f} tasks/s")
    print(f"IO任务吞吐量:      {io_speed:>10,.0f} tasks/s")
    print(f"混合模式吞吐量:    {mixed_speed:>10,.0f} tasks/s")
    print()
    
    # 评价
    if cpu_speed > 50000:
        print("✅ CPU任务性能: 优秀！")
    elif cpu_speed > 20000:
        print("✅ CPU任务性能: 良好")
    else:
        print("⚠️  CPU任务性能: 一般")
    
    if io_speed > 50000:
        print("✅ IO任务性能: 优秀！")
    elif io_speed > 20000:
        print("✅ IO任务性能: 良好")
    else:
        print("⚠️  IO任务性能: 一般")

if __name__ == "__main__":
    asyncio.run(main())


