import os
import time
import nb_log
from nb_libs.restart_programe_by_interval import restart_program
from multiprocessing import Process


print('start')

def f():
    for i in range(1000):
        time.sleep(5)
        print(os.getpid(),'hi',i)

if __name__ == '__main__':
    restart_program(10)
    Process(target=f).start()
    Process(target=f).start()
