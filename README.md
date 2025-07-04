# 1.nb_libs 介绍

nb_libs 是 各种小功能集合，不再单独给每个功能模块创建单独的git项目

# 2. 安装

pip install nb_libs


不想分开分发很多个不同功能单独的包,各种小功能杂项放在一起,具体功能看代码.


# 3. 各模块功能介绍

## 3.1 auto_git 
自动merge你自己的开发分支到指定的分支，节约10次git命令操作

## 3.2 code_line_statistics
统计代码文件和行数

## 3.4 github_git_clone
自动批量下载git项目，人工太累了。

## 3.5 global_dict
全局字典

## 3.6 http_utils

http url相关函数工具

## 3.7 lazy_importer
延迟导入，适合破解循环导入

## 3.8 path_helper
文件操作，强力的文件路径和import相互转化

## 3.9 pydantic_helper
pydantic辅助，pydantic api老是改来改去，有的在未来需要抛弃过时，直接使用官方api兼容风险很大。

## 3.10 restart_programe_by_interval.py
自动定时重启python自身，很强力很好用。
有时候python内存泄漏，每隔一周需要人工重启，定时重启就很好用，省去你苦逼找内存泄漏原因。

## 3.11 str_utils
字符串辅助，可以加密常规数据库 中间件 uri中的密码


## 3.12 sys_frame_uitils
sys._getframe 的封装，使得更好用，直接sys._getframe 来获取行号 函数名字 文件名 很难写，
很难记住方法名，EasyFrame类大幅简化


# 4 记录其他好用的三方包

icecream:
```
from icecream import ic

x = 1
ic(x)
```