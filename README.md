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


# 2. nb_time.DatetimeConverter

好用的时间转换,类型兼容强,入参可以是时间戳 字符串 datatime类型 DatetimeConverter 类型.

# 3 auto_git.GitBranchMerge

git 自动化 分支合并.

多人合作项目git开发流程一般是:

自己分支写代码 -> 自己分支commit -> 自己分支push到远程 -> 切换到开发develop分支 -> 在develop分支 git pull ->
把自己分merge到develop分支 -> develop分支 push到远程 

开发环境代码拉取develop代码重启部署,测试出现问题后,需要反复执行git繁琐的流程,整个过程如果手动人工操作git太折磨人了,
auto_git.GitBranchMerge 一键执行以上操作,如果有某一步git命令出现错误或冲突,是会中断操作的,不用担心.