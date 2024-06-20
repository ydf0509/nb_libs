import gc
import random
import sys
import time
import warnings

import pymysql


import logging
import win32con
from nb_libs.memory_leak_analysis import MemoryLeakAnalysis
from tests.t_mem_leak2 import a
from tests.t_mem_leak3 import long_list3

logging.captureWarnings(True)

logging.getLogger().setLevel(logging.ERROR)

# gc.set_debug(1)


for i in range(100):
    msg = '长字符串'*1 + str(random.random()) * 1
    warnings.warn(msg,pymysql.err.Warning,0)


# print(len(win32con.__dict__),len(str(win32con.__dict__)),sys.getsizeof(win32con))
# print(len(long_list),len(str(long_list)),sys.getsizeof(long_list))
# print(len(long_dict),len(str(long_dict)),sys.getsizeof(long_dict))

mla = MemoryLeakAnalysis()
mla.show_max_obj()

time.sleep(1000)