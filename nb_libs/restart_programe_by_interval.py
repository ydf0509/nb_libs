import sys
import os
import threading
import time
import random


# noinspection PyDefaultArgument
def restart_program(argv=sys.argv, time_sleep=60 * 60 * 3):
    """
    这个作用是每隔多少秒重启代码，不适合多进程运行的情况，适合单个进程的代码。
    :param argv:
    :param time_sleep:
    :return:
    """

    python = sys.executable

    def f():
        time_sleep_new = max(time_sleep - random.randint(0, 60),10)
        print(time_sleep_new)
        time.sleep(time_sleep_new)
        print(f'隔了{time_sleep_new}秒 重启 {argv}')
        """
        用法：

        os.execl("/usr/bin/python ", "test.py ",`'i ')这样写是不行的，

        要这样 

        os.execl("/usr/bin/python ", "python ", 'test.py ', 'i ') 
        """


        os.execl(python, python, *argv)

    threading.Thread(target=f).start()