import concurrent.futures

import asyncio
from typing import Callable, Any, Coroutine, List, TypeVar

T = TypeVar("T")  # 用于标注异步函数返回类型


class SmartAsyncPool:
    def __init__(self, max_concurrency: int = 100, max_queue_size: int = 1000):
        self._max_concurrency = max_concurrency
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._stopped = False
        self._lock = asyncio.Lock()

    async def _worker(self):
        while True:
            func, args, kwargs, fut = await self._queue.get()
            if func is None:
                # 哨兵，退出 worker
                self._queue.task_done()
                break
            try:
                result = await func(*args, **kwargs)
                if not fut.cancelled():
                    fut.set_result(result)
            except Exception as e:
                if not fut.cancelled():
                    fut.set_exception(e)
            finally:
                self._queue.task_done()

    async def _ensure_started(self):
        async with self._lock:
            if not self._running:
                self._workers = [asyncio.create_task(self._worker()) for _ in range(self._max_concurrency)]
                self._running = True



    async def submit(self,
                     func: Callable[..., Coroutine[Any, Any, T]],
                     *args,
                     block: bool = True,future: asyncio.Future=None,
                     **kwargs) -> asyncio.Future:
        """
        提交任务，返回 Future
        :param block: True 队列满等待，False 队列满立即抛异常
        """
        if self._stopped:
            raise RuntimeError("Pool is stopped, cannot submit new tasks.")

        await self._ensure_started()
        if future is None:
            future = asyncio.get_running_loop().create_future()
        try:
            if block:
                await self._queue.put((func, args, kwargs, future))
            else:
                self._queue.put_nowait((func, args, kwargs, future))
        except asyncio.QueueFull:
            future.set_exception(RuntimeError("Queue full"))
        return future

    async def run(self,
                     func: Callable[..., Coroutine[Any, Any, T]],
                     *args,
                     block: bool = True,future: asyncio.Future=None,
                     **kwargs) -> T:
        """
        await pool.execute 相当于 await await pool.submit

        :param func:
        :param args:
        :param block:
        :param kwargs:
        :return:
        """
        future: asyncio.Future = await self.submit(
            func, *args, block=block, future=future, **kwargs)
        return await future

    def sync_submit(self,
                     func: Callable[..., Coroutine[Any, Any, T]],
                     *args,
                     block: bool = True,future: asyncio.Future=None,
                    loop: asyncio.AbstractEventLoop=None,
                     **kwargs) ->concurrent.futures.Future:
        """
        同步提交任务，返回 Future
        :param block: True 队列满等待，False 队列满立即抛异常
        """
        if loop is None:
            raise ValueError("please psss loop")
        return asyncio.run_coroutine_threadsafe(self.submit(
            func, *args, block=block, future=future, **kwargs),loop)


    async def shutdown(self, wait: bool = True):
        """
        优雅关闭池
        :param wait: True 等待任务完成并 worker 退出，False 仅发哨兵后台退出
        """
        self._stopped = True

        if wait:
            # 等待队列中所有任务完成
            await self._queue.join()

        # 发送哨兵，确保所有 worker 能退出
        for _ in range(self._max_concurrency):
            await self._queue.put((None, None, None, None))

        if wait:
            # 等待所有 worker 完全退出
            await asyncio.gather(*self._workers, return_exceptions=True)

        # 清理状态
        self._workers.clear()
        self._running = False

    # =================
    # Async Context Manager
    # =================
    async def __aenter__(self):
        await self._ensure_started()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.shutdown(wait=True)


# ======================
# 示例用法
# ======================

async def sample_task(x: int):
    await asyncio.sleep(0.1)
    print(x)
    return x * 2

async def main1():
    pool = SmartAsyncPool(max_concurrency=10, max_queue_size=1000)
    # 提交任务
    futures = [await pool.submit(sample_task, i) for i in range(100)]

    # 等待任务完成
    results = await asyncio.gather(*futures)
    print("结果:", results)


async def main2():
    async with SmartAsyncPool(max_concurrency=10, max_queue_size=1000) as pool:
        for i in range(100):
            await  pool.submit(sample_task, i) # 这样不阻塞当前for循环，是丢到queue队列后不管
            await (await pool.submit(sample_task, i)) # 这样是直接得到异步函数的执行结果，阻塞当前for循环
            await pool.run(sample_task, i)  # 和上面 await (await pool.submit(sample_task, i)) 等价。





if __name__ == '__main__':
    asyncio.run(main2())
