import asyncio
import concurrent.futures
from typing import Callable, Any, Coroutine, List, TypeVar, Optional

T = TypeVar("T")  # 异步函数返回类型


class SmartAsyncPool:
    def __init__(
        self,
        max_concurrency: int = 100,
        max_queue_size: int = 1000,
        idle_timeout: float = 5.0,
    ):
        self._max_concurrency = max_concurrency
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._workers: List[asyncio.Task] = []
        self._worker_busy: dict[asyncio.Task, bool] = {}  # True: busy, False: idle
        self._running = False
        self._stopped = False
        self._lock = asyncio.Lock()
        self._idle_timeout = idle_timeout

    async def _worker(self):
        task = asyncio.current_task()
        while True:
            if self._stopped and self._queue.empty():
                break
            try:
                item = await asyncio.wait_for(self._queue.get(), timeout=self._idle_timeout)
            except asyncio.TimeoutError:
                # 空闲超时退出
                break

            func, args, kwargs, fut = item
            self._worker_busy[task] = True
            try:
                result = await func(*args, **kwargs)
                if fut and not fut.cancelled():
                    fut.set_result(result)
            except Exception as e:
                if fut and not fut.cancelled():
                    fut.set_exception(e)
            finally:
                self._queue.task_done()
                self._worker_busy[task] = False

        # Worker退出，清理记录
        async with self._lock:
            self._workers.remove(task)
            self._worker_busy.pop(task, None)

    async def _maybe_add_worker(self):
        async with self._lock:
            # 如果有空闲 Worker，不创建新 Worker
            if any(not busy for busy in self._worker_busy.values()):
                return
            # 如果还没达到最大并发，创建新的 Worker
            if len(self._workers) < self._max_concurrency:
                task = asyncio.create_task(self._worker())
                self._workers.append(task)
                self._worker_busy[task] = False

    async def submit(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args,
        block: bool = True,
        future: Optional[asyncio.Future] = None,
        **kwargs
    ) -> asyncio.Future:
        if self._stopped:
            raise RuntimeError("Pool is stopped, cannot submit new tasks.")

        if not self._running:
            self._running = True

        if future is None:
            future = asyncio.get_running_loop().create_future()

        try:
            if block:
                await self._queue.put((func, args, kwargs, future))
            else:
                self._queue.put_nowait((func, args, kwargs, future))
        except asyncio.QueueFull:
            future.set_exception(RuntimeError("Queue full"))

        # 尝试增加 Worker
        await self._maybe_add_worker()
        return future

    async def run(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args,
        block: bool = True,
        future: Optional[asyncio.Future] = None,
        **kwargs
    ) -> T:
        fut = await self.submit(func, *args, block=block, future=future, **kwargs)
        return await fut

    def sync_submit(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args,
        block: bool = True,
        future: Optional[asyncio.Future] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        **kwargs
    ) -> concurrent.futures.Future:
        if loop is None:
            raise ValueError("please pass loop")
        return asyncio.run_coroutine_threadsafe(
            self.submit(func, *args, block=block, future=future, **kwargs), loop
        )

    async def shutdown(self, wait: bool = True):
        self._stopped = True

        if wait:
            # 等待队列中所有任务完成
            await self._queue.join()

        # 等待所有 worker 退出
        if wait:
            await asyncio.gather(*self._workers, return_exceptions=True)

        # 清理状态
        self._workers.clear()
        self._worker_busy.clear()
        self._running = False

    # =================
    # Async Context Manager
    # =================
    async def __aenter__(self):
        self._running = True
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.shutdown(wait=True)


# ======================
# 示例用法
# ======================

async def sample_task(x: int):
    await asyncio.sleep(0.001)
    print(x)
    return x * 2


async def main():
    async with SmartAsyncPool(max_concurrency=10, max_queue_size=1000) as pool:
        for i in range(50):
            # 提交不阻塞
            await pool.submit(sample_task, i)

        # 阻塞获取结果
        results = [await pool.run(sample_task, i) for i in range(50, 60)]
        print("Results:", results)


if __name__ == "__main__":
    asyncio.run(main())
