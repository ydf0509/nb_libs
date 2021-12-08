
import time
import nb_log
from nb_libs.restart_programe_by_interval import restart_program
from multiprocessing import Process


print('start')

def f():
    while 1:
        time.sleep(1)
        print('hi')

if __name__ == '__main__':
    restart_program(time_sleep=12)
    Process(target=f).start()
    Process(target=f).start()
