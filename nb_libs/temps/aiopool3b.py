import signal
import time
import logging
import asyncio
import weakref
import concurrent.futures
import sys
from typing import Callable, Any, Coroutine, List, TypeVar, Optional
import atexit

T = TypeVar("T")
logger = logging.getLogger(__name__)

# 全局注册表，跟踪所有活跃的pool实例
_active_pools: weakref.WeakSet = weakref.WeakSet()

# 信号处理标记
_signal_handlers_installed = False


class SmartAsyncPool:
    def __init__(
        self,
        max_concurrency: int = 100,
        max_queue_size: int = 1000,
        min_workers: int = 1,
        idle_timeout: float = 5.0,
        auto_shutdown: bool = True,  # 自动在程序退出前等待任务完成
    ):
        self._max_concurrency = max_concurrency
        self._min_workers = min_workers
        self._max_queue_size = max_queue_size
        self._queue: Optional[asyncio.Queue] = None  # 延迟初始化
        self._workers: List[asyncio.Task] = []
        self._worker_busy: dict[asyncio.Task, bool] = {}  # True: busy, False: idle
        self._is_running = False
        self._is_shutdown = False
        self._lock: Optional[asyncio.Lock] = None  # 延迟初始化
        self._idle_timeout = idle_timeout
        self._auto_shutdown = auto_shutdown
        
        # 跟踪所有提交的future，用于自动等待
        self._pending_futures: set[asyncio.Future] = set()
        self._background_task: Optional[asyncio.Task] = None
        
        # 注册到全局池
        if self._auto_shutdown:
            _active_pools.add(self)

    def _ensure_initialized(self):
        """确保在事件循环中初始化asyncio对象"""
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=self._max_queue_size)
        if self._lock is None:
            self._lock = asyncio.Lock()
    
    async def _start(self):
        self._ensure_initialized()
        async with self._lock:
            if self._is_running:
                return
            self._is_running = True
            for _ in range(self._min_workers):
                self._create_worker()

    async def _worker(self):
        task = asyncio.current_task()
        while True:
            if self._is_shutdown and self._queue.empty():
                break
            try:
                item = await asyncio.wait_for(
                    self._queue.get(), timeout=self._idle_timeout
                )
            except asyncio.TimeoutError:
                # 空闲超时，若当前 Worker 超过最小 Worker 数量，则退出
                async with self._lock:
                    if len(self._workers) > self._min_workers:
                        break
                continue

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

        # Worker退出，清理
        async with self._lock:
            if task in self._workers:
                self._workers.remove(task)
            self._worker_busy.pop(task, None)

    def _create_worker(self):
        """在锁的保护下创建worker"""
        task = asyncio.create_task(self._worker())
        self._workers.append(task)
        self._worker_busy[task] = False
        return task

    async def _maybe_add_worker(self):
        self._ensure_initialized()
        async with self._lock:
            if len(self._workers) >= self._max_concurrency:
                return
            idle_workers = sum(1 for busy in self._worker_busy.values() if not busy)
            queue_size = self._queue.qsize()
            if queue_size > idle_workers and len(self._workers) < self._max_concurrency:
                task = self._create_worker()
                logger.debug(f'create worker {id(task)}, queue_size={queue_size}, idle_workers={idle_workers}, total_workers={len(self._workers)}')

    async def submit(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args,
        block: bool = True,
        future: Optional[asyncio.Future] = None,
        **kwargs
    ) -> asyncio.Future:
        if self._is_shutdown:
            raise RuntimeError("Pool is shutdown, cannot submit new tasks.")

        if not self._is_running:
            await self._start()
            # 注册自动清理回调（在事件循环结束前触发）
            if self._auto_shutdown and self._background_task is None:
                # self._register_auto_cleanup()
                pass
                # atexit.register(self.shutdown)

        if future is None:
            future = asyncio.get_running_loop().create_future()

        # 跟踪future，自动清理已完成的
        self._pending_futures.add(future)
        future.add_done_callback(lambda f: self._pending_futures.discard(f))

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
        self._ensure_initialized()
        async with self._lock:
            if self._is_shutdown:
                return
            self._is_shutdown = True

        if wait:
            await self._queue.join()
            
            # 只等待还未完成的worker
            active_workers = [w for w in self._workers if not w.done()]
            if active_workers:
                try:
                    await asyncio.gather(*active_workers, return_exceptions=True)
                except RuntimeError as e:
                    # 事件循环已关闭，忽略
                    if 'Event loop is closed' not in str(e):
                        raise

        async with self._lock:
            self._workers.clear()
            self._worker_busy.clear()
            self._pending_futures.clear()
            self._is_running = False

    async def __aenter__(self):
        await self._start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.shutdown(wait=True)
    

    
    # 注意：已删除有问题的 wait_for_all() 方法
    # 请使用 async_wait_for_all() 代替
    
    async def async_wait_for_all(self) -> None:
        """异步方法：等待所有pending的任务完成"""
        if self._pending_futures:
            logger.info(f"Waiting for {len(self._pending_futures)} pending tasks...")
            await asyncio.gather(*list(self._pending_futures), return_exceptions=True)
            logger.info("All tasks completed.")
    
    @property
    def pending_count(self) -> int:
        """返回当前未完成的任务数量"""
        return len(self._pending_futures)
    
    @property
    def worker_count(self) -> int:
        """返回当前worker数量"""
        return len(self._workers)
    
    @property
    def busy_worker_count(self) -> int:
        """返回繁忙的worker数量"""
        return sum(1 for busy in self._worker_busy.values() if busy)
    
    @property
    def idle_worker_count(self) -> int:
        """返回空闲的worker数量"""
        return sum(1 for busy in self._worker_busy.values() if not busy)
    
    def __repr__(self) -> str:
        """返回pool的字符串表示"""
        return (
            f"SmartAsyncPool("
            f"workers={len(self._workers)}, "
            f"busy={self.busy_worker_count}, "
            f"pending={len(self._pending_futures)}, "
            f"max={self._max_concurrency}, "
            f"running={self._is_running})"
        )
    
    async def cancel_all(self):
        """取消所有pending的任务"""
        cancelled_count = 0
        for future in list(self._pending_futures):
            if not future.done():
                future.cancel()
                cancelled_count += 1
        self._pending_futures.clear()
        logger.info(f"Cancelled {cancelled_count} pending tasks.")
        return cancelled_count


# ======================
# 智能 asyncio.run 包装器
# ======================

def smart_run(coro, *, debug=False):
    """
    智能的 asyncio.run 包装器，自动等待所有pool的pending任务完成
    
    用法:
        pool = SmartAsyncPool(auto_shutdown=True)
        
        async def main():
            await pool.submit(task, 1)
            # 不需要手动等待！
        
        smart_run(main())  # 自动等待所有pending任务
    """
    async def wrapper():
        try:
            # 执行用户的主协程
            result = await coro
            
            # 自动等待所有活跃pool的pending任务
            for pool in list(_active_pools):
                if pool.pending_count > 0:
                    logger.info(f"🔧 Auto-waiting for {pool.pending_count} pending tasks in pool...")
                    await pool.async_wait_for_all()
            
            return result
        except Exception as e:
            # 即使出错也要等待pending任务
            for pool in list(_active_pools):
                if pool.pending_count > 0:
                    logger.warning(f"⚠️  Exception occurred, but still waiting for {pool.pending_count} pending tasks...")
                    await pool.async_wait_for_all()
            raise
    
    return asyncio.run(wrapper(), debug=debug)


async def wait_for_all_aiopools_done():
    for pool in list(_active_pools):
        if pool.pending_count > 0:
            logger.info(f"🔧 Auto-waiting for {pool.pending_count} pending tasks in pool...")
            await pool.async_wait_for_all()

async def shutdown_all_pools():
    """关闭所有活跃的pool"""
    for pool in list(_active_pools):
        await pool.shutdown(wait=True)


async def cleanup_async():
    """异步清理函数：等待所有pool的pending任务"""
    logger.info("🔧 Signal received, cleaning up async pools...")
    for pool in list(_active_pools):
        if pool.pending_count > 0:
            logger.info(f"⏳ Waiting for {pool.pending_count} pending tasks in pool...")
            await pool.async_wait_for_all()
    logger.info("✅ All pools cleaned up.")

def cleanup_sync_handler(signum=None, frame=None):
    """同步信号处理器：将清理任务提交到事件循环"""
    logger.info(f"📡 Received signal {signum}, initiating cleanup...")
    
    try:
        # 尝试获取当前事件循环
        loop = asyncio.get_running_loop()
        # 在当前循环中创建清理任务
        asyncio.create_task(cleanup_async())
    except RuntimeError:
        # 没有运行中的事件循环，尝试创建新的
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(cleanup_async(), loop)
            else:
                loop.run_until_complete(cleanup_async())
        except Exception as e:
            logger.error(f"❌ Failed to cleanup: {e}")
    

atexit.register(cleanup_sync_handler)



if __name__ == "__main__":
        # ======================
    # 示例用法
    # ======================

    async def sample_task(x: int):
        await asyncio.sleep(0.1)
        print(time.strftime("%H:%M:%S"),x,id(asyncio.current_task()))
        return x * 2

    async def main():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        async with SmartAsyncPool(max_concurrency=100, max_queue_size=1000, min_workers=2) as pool:
            # 提交不阻塞
            for i in range(90):
                await pool.submit(sample_task, i)
            
            await asyncio.sleep(15)

            for i in range(100):
                await asyncio.sleep(0.2)
                await pool.submit(sample_task, i)

            for i in range(100, 1000):
                await pool.submit(sample_task, i)

            # # 阻塞获取结果
            # results = [await pool.run(sample_task, i) for i in range(1000, 3000)]
            # print("Results:", results)
    
    # ========= 测试1：传统方式（手动await） =========
    print("\n" + "="*50)
    print("测试1：手动await future")
    print("="*50)
    pool1 = SmartAsyncPool(max_concurrency=100, max_queue_size=1000, min_workers=2)
    async def test_manual_await():
        future = await pool1.submit(sample_task, 1)
        result = await future
        print(f"✅ Task result: {result}")
        await pool1.shutdown(wait=True)
    
    asyncio.run(test_manual_await())
    
    # ========= 测试2：智能模式（忘记await，自动等待） =========
    print("\n" + "="*50)
    print("测试2：忘记await future，但启用auto_shutdown")
    print("="*50)
    pool2 = SmartAsyncPool(max_concurrency=100, min_workers=0, auto_shutdown=True)
    async def test_auto_wait():
        # 故意不await future，模拟用户忘记等待
        await pool2.submit(sample_task, 10)
        await pool2.submit(sample_task, 11)
        await pool2.submit(sample_task, 12)
        print(f"📊 提交了3个任务，pending count: {pool2.pending_count}")
        
        # 用户可以主动调用等待
        await pool2.async_wait_for_all()
        print(f"✅ 所有任务完成！pending count: {pool2.pending_count}")
    
    asyncio.run(test_auto_wait())
    
    # ========= 测试3：使用 smart_run (完全自动) =========
    print("\n" + "="*50)
    print("测试3：使用 smart_run - 完全不需要手动等待！")
    print("="*50)
    pool3 = SmartAsyncPool(max_concurrency=100, min_workers=0, auto_shutdown=True)
    async def test_smart_run():
        # 只提交，啥都不管！
        await pool3.submit(sample_task, 30)
        await pool3.submit(sample_task, 31)
        await pool3.submit(sample_task, 32)
        print(f"📊 提交了3个任务，pending count: {pool3.pending_count}")
        print("✨ 用户不需要等待，smart_run会自动处理！")
        # 直接退出，不用await，不用shutdown
    
    smart_run(test_smart_run())  # 使用 smart_run 而不是 asyncio.run
    
    # ========= 测试4：普通 asyncio.run + 自动信号处理 =========
    print("\n" + "="*50)
    print("测试4：使用普通 asyncio.run，完全不手动等待！")
    print("="*50)
    pool4 = SmartAsyncPool(max_concurrency=100, min_workers=0, auto_shutdown=True)
    async def test_auto_signal():
        await pool4.submit(sample_task, 40)
        await pool4.submit(sample_task, 41)
        await pool4.submit(sample_task, 42)
        print(f"📊 提交了3个任务，pending count: {pool4.pending_count}")
        print("✨ 没有手动等待，但信号处理器已安装！")
        print("💡 如果用 Ctrl+C 中断，会自动等待任务完成")
        
        # 等一下让任务执行
        # await asyncio.sleep(0.2)
        
        # ✅ 任务应该已经完成了
        print(f"📊 0.2秒后，pending count: {pool4.pending_count}")
    
    asyncio.run(test_auto_signal())
   

