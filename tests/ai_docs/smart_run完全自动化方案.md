# smart_run 完全自动化方案

## 🎯 终极目标

**让用户完全不需要关心任务是否完成，就像使用线程池一样简单！**

---

## ❌ 问题：用户忘记等待

### 传统方式的痛点

```python
pool = SmartAsyncPool()

async def main():
    await pool.submit(task, 1)
    await pool.submit(task, 2)
    # 用户忘记等待就退出了

asyncio.run(main())  # 任务丢失！💀
```

### 即使有 async_wait_for_all 也需要用户记住

```python
pool = SmartAsyncPool()

async def main():
    await pool.submit(task, 1)
    await pool.submit(task, 2)
    # 还是需要用户记住调用
    await pool.async_wait_for_all()  # ❌ 仍然需要手动！

asyncio.run(main())
```

**问题**：用户必须记住调用 `async_wait_for_all()`，否则任务丢失！

---

## ✅ 解决方案：`smart_run()`

### 核心思想

**用 `smart_run` 替代 `asyncio.run`，自动等待所有pending任务！**

```python
pool = SmartAsyncPool(auto_shutdown=True)

async def main():
    await pool.submit(task, 1)
    await pool.submit(task, 2)
    # 啥都不用管，直接退出！

smart_run(main())  # ✅ 自动等待所有任务完成！
```

---

## 🔧 实现原理

### 1. 全局注册表

```python
import weakref

# 全局跟踪所有启用auto_shutdown的pool
_active_pools: weakref.WeakSet = weakref.WeakSet()

class SmartAsyncPool:
    def __init__(self, auto_shutdown=True):
        if auto_shutdown:
            _active_pools.add(self)  # 注册到全局
```

**好处**：
- 使用 `WeakSet`，不阻止pool被垃圾回收
- 自动跟踪所有需要清理的pool

### 2. smart_run 包装器

```python
def smart_run(coro, *, debug=False):
    """智能的 asyncio.run 包装器"""
    async def wrapper():
        try:
            # 1. 执行用户的主协程
            result = await coro
            
            # 2. 自动等待所有pool的pending任务
            for pool in list(_active_pools):
                if pool.pending_count > 0:
                    logger.info(f"🔧 Auto-waiting for {pool.pending_count} tasks...")
                    await pool.async_wait_for_all()
            
            return result
        except Exception as e:
            # 3. 即使出错也等待pending任务
            for pool in list(_active_pools):
                if pool.pending_count > 0:
                    logger.warning(f"⚠️ Still waiting for {pool.pending_count} tasks...")
                    await pool.async_wait_for_all()
            raise
    
    return asyncio.run(wrapper(), debug=debug)
```

**关键点**：
- ✅ 在用户主协程完成后自动检查
- ✅ 自动等待所有pending任务
- ✅ 即使异常也会等待（防止任务丢失）
- ✅ 完全透明，用户无感知

---

## 📖 使用示例

### 方式1：完全懒惰（推荐）

```python
from nb_libs.temps.aiopool3 import SmartAsyncPool, smart_run

pool = SmartAsyncPool(auto_shutdown=True)

async def main():
    # 只管提交，啥都不管
    for i in range(100):
        await pool.submit(download_file, i)
    
    # 直接退出，不需要任何等待代码！

smart_run(main())  # ✅ 自动等待所有任务完成
```

**输出**：
```
📊 提交了100个任务
🔧 Auto-waiting for 100 pending tasks in pool...
✅ All pending tasks completed.
```

### 方式2：多个pool

```python
pool1 = SmartAsyncPool(auto_shutdown=True)
pool2 = SmartAsyncPool(auto_shutdown=True)

async def main():
    # 提交到不同的pool
    await pool1.submit(task, 1)
    await pool2.submit(task, 2)
    
    # 啥都不管

smart_run(main())  # ✅ 自动等待所有pool的任务
```

### 方式3：异常安全

```python
pool = SmartAsyncPool(auto_shutdown=True)

async def main():
    await pool.submit(task, 1)
    await pool.submit(task, 2)
    
    raise ValueError("Something went wrong!")  # 💥

try:
    smart_run(main())
except ValueError:
    pass

# ✅ 即使发生异常，任务也会完成！
```

---

## 🔄 与其他方式对比

### 方式1：完全不管（❌ 任务丢失）

```python
pool = SmartAsyncPool()

async def main():
    await pool.submit(task, 1)

asyncio.run(main())  # ❌ 任务丢失
```

### 方式2：手动 await future（✅ 但麻烦）

```python
pool = SmartAsyncPool()

async def main():
    future = await pool.submit(task, 1)
    await future  # ✅ 需要记住await

asyncio.run(main())
```

### 方式3：手动 async_wait_for_all（✅ 但仍需记住）

```python
pool = SmartAsyncPool()

async def main():
    await pool.submit(task, 1)
    await pool.async_wait_for_all()  # ✅ 需要记住调用

asyncio.run(main())
```

### 方式4：smart_run（✅ 完全自动）

```python
pool = SmartAsyncPool(auto_shutdown=True)

async def main():
    await pool.submit(task, 1)
    # 啥都不用管

smart_run(main())  # ✅ 完全自动，零心智负担
```

---

## 📊 功能对比表

| 方式 | 需要手动await? | 任务安全? | 心智负担 | 推荐度 |
|-----|--------------|----------|---------|--------|
| 直接asyncio.run | 是 | ❌ | 高 | ⭐ |
| await future | 是 | ✅ | 中 | ⭐⭐⭐ |
| async_wait_for_all | 是 | ✅ | 中 | ⭐⭐⭐⭐ |
| **smart_run** | **否** | **✅** | **零** | **⭐⭐⭐⭐⭐** |

---

## 🎯 最佳实践

### ✅ 推荐用法

```python
from nb_libs.temps.aiopool3 import SmartAsyncPool, smart_run

# 1. 创建pool时启用auto_shutdown
pool = SmartAsyncPool(auto_shutdown=True)

# 2. 使用 smart_run 而不是 asyncio.run
async def main():
    for i in range(1000):
        await pool.submit(task, i)
    # 不需要任何等待代码

smart_run(main())  # 自动处理一切
```

### 🔧 高级用法：部分等待

```python
pool = SmartAsyncPool(auto_shutdown=True)

async def main():
    # 紧急任务：立即等待
    result = await pool.run(urgent_task, 1)
    
    # 普通任务：fire-and-forget
    for i in range(100):
        await pool.submit(normal_task, i)
    
    # 不需要等待，smart_run会自动处理

smart_run(main())
```

### 🎨 实时监控

```python
pool = SmartAsyncPool(auto_shutdown=True)

async def main():
    # 提交任务
    for i in range(100):
        await pool.submit(task, i)
    
    # 可选：监控进度（但不是必须的）
    while pool.pending_count > 10:
        print(f"Still have {pool.pending_count} tasks...")
        await asyncio.sleep(1)
    
    # 剩余任务由smart_run自动等待

smart_run(main())
```

---

## ⚙️ 配置选项

### auto_shutdown 参数

```python
# 启用自动等待（推荐）
pool = SmartAsyncPool(auto_shutdown=True)

# 禁用自动等待（需要手动管理）
pool = SmartAsyncPool(auto_shutdown=False)
```

| auto_shutdown | 行为 | 适用场景 |
|--------------|------|---------|
| `True` (推荐) | 自动注册到全局，smart_run会等待 | 大部分场景 |
| `False` | 不自动等待，需要手动管理 | 需要精确控制的场景 |

---

## 🚀 性能说明

### 零开销

`smart_run` 的开销几乎为零：

1. **全局注册**：使用 `WeakSet`，O(1)添加
2. **检查pending**：只在主协程结束后检查一次
3. **等待任务**：只在有pending任务时才等待

### 性能对比

```python
# 方式1：手动await每个future
futures = []
for i in range(10000):
    fut = await pool.submit(task, i)
    futures.append(fut)
await asyncio.gather(*futures)

# 方式2：smart_run自动等待
for i in range(10000):
    await pool.submit(task, i)
# 自动等待

# 性能完全相同！
```

---

## 🎉 总结

### smart_run = asyncio.run + 智能等待

**三大核心优势**：

1. **完全自动** 🤖
   - 不需要手动await
   - 不需要手动shutdown
   - 不需要记住任何清理代码

2. **任务安全** 🛡️
   - 防止任务丢失
   - 异常安全
   - 自动清理

3. **零心智负担** 🧠
   - 用法和 asyncio.run 完全一样
   - 只需要把 `asyncio.run` 改成 `smart_run`
   - 像使用线程池一样简单

### 使用建议

| 场景 | 推荐方案 |
|-----|---------|
| 新项目 | **smart_run** + auto_shutdown=True |
| 需要精确控制 | async with + manual shutdown |
| 需要实时监控 | pending_count + async_wait_for_all |
| 批量任务 | smart_run（完全不用管） |

---

## 🎯 一句话总结

**只需要把 `asyncio.run` 改成 `smart_run`，就能像使用线程池一样简单，完全不用担心任务丢失！**

```python
# ❌ 旧代码
asyncio.run(main())

# ✅ 新代码（只改一个词）
smart_run(main())
```

就这么简单！🎉

