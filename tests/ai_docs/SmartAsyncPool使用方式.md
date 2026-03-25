# SmartAsyncPool 使用方式指南

## 问题：为什么不用with时程序会快速退出？

### ❌ 错误示例
```python
pool = SmartAsyncPool(max_concurrency=100)

async def main():
    await pool.submit(task, 1)  # 只是提交任务，不等待
    # main函数结束，程序退出，worker还没来得及执行

asyncio.run(main())
```

**原因**：
- `submit()` 只是把任务放入队列，立即返回Future
- 如果不 `await` 这个Future，程序就会继续执行
- main函数结束 → asyncio.run退出 → 事件循环关闭 → worker没机会执行

---

## ✅ 正确使用方式

### 方式1：使用 async with（推荐）

```python
async def main():
    async with SmartAsyncPool(max_concurrency=100) as pool:
        await pool.submit(task, 1)
        await pool.submit(task, 2)
        # 退出with块时，会自动调用 pool.shutdown(wait=True)
        # 等待所有任务完成
```

**优点**：
- ✅ 自动管理生命周期
- ✅ 自动等待所有任务完成
- ✅ 自动清理资源
- ✅ 异常安全

---

### 方式2：手动 await Future

```python
pool = SmartAsyncPool(max_concurrency=100)

async def main():
    # 提交任务并获取future
    future1 = await pool.submit(task, 1)
    future2 = await pool.submit(task, 2)
    
    # 等待任务完成
    result1 = await future1
    result2 = await future2
    
    print(f"Results: {result1}, {result2}")
    
    # 可选：手动关闭pool
    await pool.shutdown(wait=True)

asyncio.run(main())
```

**优点**：
- ✅ 灵活控制每个任务
- ✅ 可以获取返回值
- ✅ 可以单独处理异常

---

### 方式3：使用 run() 方法

```python
pool = SmartAsyncPool(max_concurrency=100)

async def main():
    # run() = submit() + await future
    result1 = await pool.run(task, 1)  # 提交并等待完成
    result2 = await pool.run(task, 2)
    
    print(f"Results: {result1}, {result2}")
    
    await pool.shutdown(wait=True)

asyncio.run(main())
```

**优点**：
- ✅ 简洁，一步到位
- ✅ 自动等待结果
- ✅ 适合需要立即获取结果的场景

---

### 方式4：批量提交 + gather

```python
pool = SmartAsyncPool(max_concurrency=100)

async def main():
    # 批量提交任务
    futures = []
    for i in range(100):
        fut = await pool.submit(task, i)
        futures.append(fut)
    
    # 等待所有任务完成
    results = await asyncio.gather(*futures)
    print(f"All results: {results}")
    
    await pool.shutdown(wait=True)

asyncio.run(main())
```

**优点**：
- ✅ 并发执行大量任务
- ✅ 统一收集结果
- ✅ 高性能

---

### 方式5：Fire-and-forget（不等待结果）

```python
pool = SmartAsyncPool(max_concurrency=100)

async def main():
    # 提交任务但不保存future
    for i in range(100):
        await pool.submit(task, i)
    
    # 方案A：等待队列清空
    await pool._queue.join()
    
    # 方案B：手动等待一段时间
    await asyncio.sleep(10)
    
    # 方案C：使用shutdown等待所有任务完成
    await pool.shutdown(wait=True)

asyncio.run(main())
```

**适用场景**：
- 不关心任务返回值
- 只需要确保任务执行完成
- 适合日志记录、数据清理等任务

---

## 🔄 完整对比示例

```python
from nb_libs.temps.aiopool3 import SmartAsyncPool
import asyncio

async def my_task(x: int):
    await asyncio.sleep(0.1)
    print(f"Task {x} done")
    return x * 2

# ===== 方式1: async with (推荐) =====
async def example1():
    async with SmartAsyncPool(max_concurrency=10) as pool:
        for i in range(50):
            await pool.submit(my_task, i)
    # 自动等待所有任务完成
    print("All done!")

# ===== 方式2: 手动管理 =====
async def example2():
    pool = SmartAsyncPool(max_concurrency=10)
    
    # 提交任务
    futures = [await pool.submit(my_task, i) for i in range(50)]
    
    # 等待完成
    results = await asyncio.gather(*futures)
    print(f"Results: {results}")
    
    # 关闭pool
    await pool.shutdown(wait=True)

# ===== 方式3: run方法 =====
async def example3():
    pool = SmartAsyncPool(max_concurrency=10)
    
    # 串行执行（每个任务等待完成后再提交下一个）
    for i in range(10):
        result = await pool.run(my_task, i)
        print(f"Got result: {result}")
    
    await pool.shutdown(wait=True)

# ===== 方式4: 混合使用 =====
async def example4():
    pool = SmartAsyncPool(max_concurrency=10)
    
    # 快速提交一批任务
    futures = []
    for i in range(20):
        fut = await pool.submit(my_task, i)
        futures.append(fut)
    
    # 立即执行并等待一个紧急任务
    urgent_result = await pool.run(my_task, 999)
    print(f"Urgent done: {urgent_result}")
    
    # 等待之前的批量任务
    await asyncio.gather(*futures)
    
    await pool.shutdown(wait=True)

# 运行
asyncio.run(example1())
```

---

## 📋 选择建议

| 场景 | 推荐方式 | 原因 |
|-----|---------|------|
| 一般使用 | `async with` | 自动管理，最安全 |
| 需要返回值 | `await future` 或 `run()` | 可以获取结果 |
| 大批量任务 | `submit` + `gather` | 高并发性能 |
| 长期运行的pool | 手动管理 + `shutdown()` | 灵活控制生命周期 |
| 不关心结果 | `submit` + `queue.join()` | Fire-and-forget |

---

## ⚠️ 常见错误

### 错误1：忘记await

```python
# ❌ 错误
async def bad():
    pool = SmartAsyncPool()
    pool.submit(task, 1)  # 没有await
    # 程序立即退出

# ✅ 正确
async def good():
    pool = SmartAsyncPool()
    future = await pool.submit(task, 1)  # await submit
    await future  # await future
```

### 错误2：在with外使用pool

```python
# ❌ 错误
async def bad():
    async with SmartAsyncPool() as pool:
        pass
    
    await pool.submit(task, 1)  # pool已经shutdown了！

# ✅ 正确
async def good():
    async with SmartAsyncPool() as pool:
        await pool.submit(task, 1)
```

### 错误3：混淆submit和run

```python
# submit: 立即返回future，不等待
future = await pool.submit(task, 1)  # 任务已提交，但可能还没执行
result = await future  # 等待执行完成

# run: 提交并等待完成
result = await pool.run(task, 1)  # 一步到位
```

---

## 🎯 总结

**核心原则**：
1. `submit()` 只是提交任务，必须 `await` 返回的 Future 才能等待完成
2. `run()` = `submit()` + `await future`，一步到位
3. 使用 `async with` 可以自动管理生命周期
4. 不使用 `with` 时，记得手动 `shutdown(wait=True)`

**记住**：异步任务需要明确等待，否则程序会在任务完成前退出！

