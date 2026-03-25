"""
测试 ThreadPoolExecutor 的自动等待行为
"""
import time
import concurrent.futures
import weakref

print("="*60)
print("测试1: ThreadPoolExecutor 不使用 with，会自动等待吗？")
print("="*60)

def task(n):
    time.sleep(0.1)
    print(f"Task {n} done!")
    return n

# 不使用 with
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
executor.submit(task, 1)
executor.submit(task, 2)
executor.submit(task, 3)
print("Main: submitted 3 tasks, exiting...")
# 注意：没有调用 shutdown()，没有 with

# 程序退出时会发生什么？
print("\n等待程序自然退出...")

