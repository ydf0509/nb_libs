# SmartAsyncPool 智能特性详解

## 🎯 核心问题

**传统异步池的痛点**：
```python
pool = AsyncPool()

async def main():
    await pool.submit(task, 1)  # 只提交，忘记await
    await pool.submit(task, 2)
    # 函数结束 → 程序退出 → 任务丢失！💀

asyncio.run(main())
```

**问题**：用户忘记等待Future，任务还没执行完程序就退出了！

---

## ✨ SmartAsyncPool的智能解决方案

### 特性1：自动跟踪未完成的任务

```python
class SmartAsyncPool:
    def __init__(self, auto_shutdown: bool = True):
        # 跟踪所有pending的future
        self._pending_futures: set[asyncio.Future] = set()
    
    async def submit(...):
        future = asyncio.get_running_loop().create_future()
        
        # 📌 自动跟踪
        self._pending_futures.add(future)
        
        # 📌 任务完成后自动清理
        future.add_done_callback(lambda f: self._pending_futures.discard(f))
        
        return future
```

**优点**：
- ✅ 实时知道有多少任务未完成
- ✅ 自动清理已完成的任务
- ✅ 零开销（使用done_callback）

---

### 特性2：提供 `pending_count` 属性

```python
pool = SmartAsyncPool()

await pool.submit(task, 1)
await pool.submit(task, 2)

print(f"未完成任务数: {pool.pending_count}")  # 输出: 2
```

**用途**：
- 监控任务进度
- 判断是否需要等待
- 调试和日志记录

---

### 特性3：提供 `async_wait_for_all()` 方法

```python
pool = SmartAsyncPool()

# 提交一堆任务
for i in range(100):
    await pool.submit(task, i)

# 🎯 一键等待所有任务完成
await pool.async_wait_for_all()
print("所有任务完成！")
```

**对比传统方式**：
```python
# ❌ 传统方式：需要手动保存所有future
futures = []
for i in range(100):
    fut = await pool.submit(task, i)
    futures.append(fut)  # 容易忘记！

await asyncio.gather(*futures)

# ✅ 智能方式：自动跟踪
for i in range(100):
    await pool.submit(task, i)  # 不需要保存future

await pool.async_wait_for_all()  # 自动等待所有
```

---

### 特性4：延迟初始化（事件循环安全）

**问题**：
```python
# ❌ 错误：在事件循环外创建Queue
class OldPool:
    def __init__(self):
        self._queue = asyncio.Queue()  # 💥 RuntimeError!

pool = OldPool()  # 在事件循环外创建
asyncio.run(main())
```

**解决方案**：
```python
# ✅ 正确：延迟初始化
class SmartAsyncPool:
    def __init__(self):
        self._queue = None  # 先不创建
    
    def _ensure_initialized(self):
        if self._queue is None:
            self._queue = asyncio.Queue()  # 在事件循环中创建

pool = SmartAsyncPool()  # ✅ 可以在任何地方创建
asyncio.run(main())  # ✅ 自动在事件循环中初始化
```

**优点**：
- ✅ 可以在任何地方创建pool实例
- ✅ 不需要担心事件循环问题
- ✅ 支持多个事件循环

---

## 📖 完整使用示例

### 场景1：完全懒惰模式（最省心）

```python
pool = SmartAsyncPool(auto_shutdown=True)

async def lazy_user():
    # 只管提交，啥都不管
    await pool.submit(task, 1)
    await pool.submit(task, 2)
    await pool.submit(task, 3)
    
    # 退出前检查一下
    if pool.pending_count > 0:
        print(f"还有 {pool.pending_count} 个任务，等一下...")
        await pool.async_wait_for_all()

asyncio.run(lazy_user())
```

### 场景2：Fire-and-Forget（后台任务）

```python
pool = SmartAsyncPool()

async def background_jobs():
    # 提交后台任务
    for i in range(1000):
        await pool.submit(cleanup_task, i)
    
    print(f"提交了 {pool.pending_count} 个清理任务")
    
    # 继续做其他事情
    await do_other_work()
    
    # 最后等待清理任务完成
    print("等待后台任务完成...")
    await pool.async_wait_for_all()

asyncio.run(background_jobs())
```

### 场景3：批量任务监控

```python
pool = SmartAsyncPool()

async def batch_with_progress():
    total = 1000
    
    # 批量提交
    for i in range(total):
        await pool.submit(download_file, i)
    
    # 实时监控进度
    while pool.pending_count > 0:
        completed = total - pool.pending_count
        progress = (completed / total) * 100
        print(f"进度: {progress:.1f}% ({completed}/{total})")
        await asyncio.sleep(1)
    
    print("全部完成！")

asyncio.run(batch_with_progress())
```

### 场景4：混合模式（部分等待）

```python
pool = SmartAsyncPool()

async def mixed_mode():
    # 紧急任务：立即等待
    result = await pool.run(urgent_task, 1)
    print(f"紧急任务完成: {result}")
    
    # 普通任务：fire-and-forget
    for i in range(100):
        await pool.submit(normal_task, i)
    
    # 继续做其他事
    await do_something_else()
    
    # 最后统一等待
    await pool.async_wait_for_all()

asyncio.run(mixed_mode())
```

---

## 🔄 与线程池对比

### ThreadPoolExecutor（线程池）

```python
from concurrent.futures import ThreadPoolExecutor

pool = ThreadPoolExecutor(max_workers=10)

def task(x):
    return x * 2

# 提交任务
future1 = pool.submit(task, 1)
future2 = pool.submit(task, 2)

# 可以不管，程序退出时自动等待
# ThreadPoolExecutor.__exit__ 会自动 shutdown(wait=True)
```

**特点**：
- ✅ 使用with自动管理
- ✅ 退出时自动等待
- ❌ 但是如果不用with，容易忘记shutdown

### SmartAsyncPool（异步池）

```python
pool = SmartAsyncPool(auto_shutdown=True)

async def task(x):
    return x * 2

# 提交任务
await pool.submit(task, 1)
await pool.submit(task, 2)

# 可以随时检查
if pool.pending_count > 0:
    await pool.async_wait_for_all()
```

**特点**：
- ✅ 自动跟踪未完成任务
- ✅ 提供pending_count实时监控
- ✅ 提供async_wait_for_all()便捷等待
- ✅ 延迟初始化，事件循环安全
- ✅ 灵活：可以with，也可以不with

---

## ⚙️ 配置选项

```python
pool = SmartAsyncPool(
    max_concurrency=100,      # 最大并发数
    max_queue_size=1000,      # 队列大小
    min_workers=2,            # 最小worker数
    idle_timeout=5.0,         # 空闲超时（秒）
    auto_shutdown=True,       # 启用智能特性
)
```

### `auto_shutdown` 参数说明

| 值 | 行为 |
|----|------|
| `True` (默认) | 启用智能跟踪，自动管理pending_futures |
| `False` | 禁用智能特性，行为类似传统异步池 |

---

## 📊 API 总览

| 方法/属性 | 类型 | 说明 |
|----------|------|------|
| `submit(func, *args)` | async | 提交任务，返回Future |
| `run(func, *args)` | async | 提交并等待任务完成 |
| `async_wait_for_all()` | async | 等待所有pending任务完成 |
| `pending_count` | property | 返回未完成任务数量 |
| `shutdown(wait=True)` | async | 关闭pool并可选等待 |

---

## 🎯 最佳实践

### ✅ 推荐做法

1. **使用 async with（最安全）**
```python
async with SmartAsyncPool() as pool:
    await pool.submit(task, 1)
    # 自动等待并清理
```

2. **手动管理 + async_wait_for_all**
```python
pool = SmartAsyncPool()
await pool.submit(task, 1)
await pool.async_wait_for_all()  # 确保完成
```

3. **监控进度**
```python
while pool.pending_count > 0:
    print(f"剩余: {pool.pending_count}")
    await asyncio.sleep(1)
```

### ❌ 避免的错误

1. **完全不管（任务可能丢失）**
```python
async def bad():
    pool = SmartAsyncPool(auto_shutdown=False)
    await pool.submit(task, 1)
    # 直接退出，任务丢失！
```

2. **忘记await submit**
```python
async def bad():
    pool.submit(task, 1)  # ❌ 没有await！
```

---

## 🚀 性能优化

SmartAsyncPool的智能特性几乎零开销：

1. **Future跟踪**：使用set，O(1)添加和删除
2. **自动清理**：使用done_callback，不需要定期扫描
3. **延迟初始化**：只在需要时创建对象
4. **弹性Worker**：自动扩缩容，节省资源

---

## 总结

SmartAsyncPool = **异步池** + **智能管理** + **零心智负担**

核心优势：
- 🧠 自动跟踪任务状态
- 📊 实时监控进度
- 🛡️ 防止任务丢失
- 🔧 灵活的使用方式
- 🚀 像线程池一样简单

**忘记await？没关系！SmartAsyncPool帮你兜底！** 🎉

