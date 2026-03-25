
import asyncio
from typing import Callable, Any, List


class AutoStartAsyncioPool:
    def __init__(self, max_concurrency: int = 100, max_queue_size: int = 1000):
        self._max_concurrency = max_concurrency
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._lock = asyncio.Lock()  # 确保只启动一次

    async def _worker(self):
        while True:
            coro_func, args, kwargs, fut = await self._queue.get()
            if coro_func is None:
                self._queue.task_done()
                break
            try:
                result = await coro_func(*args, **kwargs)
                fut.set_result(result)
            except Exception as e:
                fut.set_exception(e)
            finally:
                self._queue.task_done()

    async def _ensure_started(self):
        """自动启动 worker"""
        async with self._lock:
            if not self._running:
                self._workers = [asyncio.create_task(self._worker()) for _ in range(self._max_concurrency)]
                self._running = True

    async def submit(self, coro_func: Callable[..., Any], *args, block: bool = True, **kwargs) -> asyncio.Future:
        """
        提交任务，立即返回 Future
        :param block: True 队列满了就等待，False 队列满直接抛异常
        """
        await self._ensure_started()  # 第一次 submit 自动启动 worker
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        if block:
            await self._queue.put((coro_func, args, kwargs, fut))
        else:
            self._queue.put_nowait((coro_func, args, kwargs, fut))
        return fut

    async def shutdown(self, wait: bool = True):
        """关闭池"""
        if not self._running:
            return
        if wait:
            # 等待队列中所有任务完成
            await self._queue.join()
        for _ in range(self._max_concurrency):
            await self._queue.put((None, None, None, None))
        if wait:
            await asyncio.gather(*self._workers)
        self._workers.clear()
        self._running = False


if __name__ == "__main__":
    import httpx
    import aiohttp
    import asyncio
    import time
    from system_monitoring import start_all_monitoring_threads,thread_show_process_cpu_usage

    thread_show_process_cpu_usage()

    url = "http://127.0.0.1:8006/aio2"


    async def aio_req(client, n):
        resp = await client.get(url)
        print(f"{time.strftime('%H:%M:%S')} aio_req {n} {resp.status_code}")
        return n, resp.status_code


    async def aio_req2(session: aiohttp.ClientSession, n: int):
        async with session.get(url) as resp:
            text = await resp.text()
            print(f"{time.strftime('%H:%M:%S')} aio_req {n} {resp.status} ")
            return n, resp.status, text

    async def main():
        pool = AutoStartAsyncioPool(max_concurrency=10, max_queue_size=500)

        # limits = httpx.Limits(max_connections=150, max_keepalive_connections=150)
        # async with httpx.AsyncClient(limits=limits, timeout=30) as client:
        connector = aiohttp.TCPConnector(limit=300, force_close=False)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            futures = []
            for i in range(50000):
                # 第一次 submit 自动启动 worker
                fut = await pool.submit(aio_req2, session, i, block=True)
                futures.append(fut)

        # 	start = time.time()
        # 	results = await asyncio.gather(*futures)
        # 	end = time.time()
        #
        # await pool.shutdown()
        # print(f"完成 {len(results)} 个请求, 用时 {end - start:.2f} 秒")
        # print(results[:10])


    # asyncio.run(main())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()

