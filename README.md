# 各种日常工具

# 安装

pip install nb_libs

# 1. restart_program每隔多久重启代码自身。

```python
import time
import datetime
from nb_libs.restart_programe_by_interval import restart_program


def _run():
    print(datetime.datetime.now(), '开始运行程序')
    for i in range(1000):
        time.sleep(0.5)
        print(datetime.datetime.now(), i)


if __name__ == '__main__':
    restart_program(10)  # 每隔10秒重启。
    _run()
```
