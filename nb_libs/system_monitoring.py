

import psutil
import os
import time
import threading
import nb_log

logger = nb_log.get_logger(__name__)

def show_process_cpu_usage(interval):
    while True:
        pid = os.getpid()
        p = psutil.Process(pid)
        cpu_percent = p.cpu_percent(interval=0.1)  # 每1秒计算一次使用率
        time.sleep(interval)
        # print(logger.level,logger.handlers)
        logger.info(f"{time.strftime('%Y-%m-%d %H:%M:%S')} 进程 {pid} 的CPU使用率: {cpu_percent:.2f}%")

def thread_show_process_cpu_usage(interval=1):
    threading.Thread(target=show_process_cpu_usage,args=(interval,),daemon=True).start()


def show_system_cpu_usage(interval=1):
    while True:
        cpu_percent = psutil.cpu_percent(interval=0.1)  # 每1秒计算一次使用率
        time.sleep(interval)
        logger.info(f"{time.strftime('%Y-%m-%d %H:%M:%S')} 系统CPU使用率: {cpu_percent:.2f}%")

def thread_show_system_cpu_usage(interval=1):
    threading.Thread(target=show_system_cpu_usage,args=(interval,),daemon=True).start()


def show_cpu_per_core(interval=1):
    while True:
        per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        time.sleep(interval)
        str_all = ""
        for i, p in enumerate(per_core):
            str_all += f"\nCPU核心{i:2} 占用率: {p}%"
        logger.info(str_all)

def thread_show_cpu_per_core(interval=1):
    threading.Thread(target=show_cpu_per_core,args=(interval,),daemon=True).start()


def show_system_memory_usage(interval=1):
    while True:
        time.sleep(interval)
        mem = psutil.virtual_memory()
        logger.info(f"{time.strftime('%Y-%m-%d %H:%M:%S')} 系统内存占用: {mem.percent}%")


def thread_show_system_memory_usage(interval=1):
    threading.Thread(target=show_system_memory_usage,args=(interval,),daemon=True).start()


def show_process_memory_usage(interval=1):
    while True:
        time.sleep(interval)
        pid = os.getpid()
        p = psutil.Process(pid)
        mem = p.memory_info()
        logger.info(f"{time.strftime('%Y-%m-%d %H:%M:%S')} 进程 {pid} 的内存占用: {mem.rss / (1024 * 1024):.2f} MB")


def thread_show_process_memory_usage(interval=1):
    threading.Thread(target=show_process_memory_usage,args=(interval,),daemon=True).start()


def show_system_disk_usage(interval=1):
    while True:
        time.sleep(interval)
        disk = psutil.disk_usage('/')
        logger.info(f"{time.strftime('%Y-%m-%d %H:%M:%S')} 系统磁盘占用: {disk.percent}%")


def thread_show_system_disk_usage(interval=1):
    threading.Thread(target=show_system_disk_usage,args=(interval,),daemon=True).start()


def start_all_monitoring_threads(interval=1):
    thread_show_process_cpu_usage(interval=interval)
    thread_show_system_cpu_usage(interval=interval)
    thread_show_cpu_per_core(interval=interval)
    thread_show_system_memory_usage(interval=interval)
    thread_show_process_memory_usage(interval=interval)
    thread_show_system_disk_usage(interval=interval)

def thread_show_process_cpu_and_memory_usage(interval=1):
    thread_show_process_memory_usage(interval=interval)
    thread_show_process_cpu_usage(interval=interval)

def test_use_cpu():
    """
    无限懵逼死循环，超高速占用CPU
    :return:
    """
    while True:
        pass

if __name__ == '__main__':
    start_all_monitoring_threads(interval=10)
    test_use_cpu()
