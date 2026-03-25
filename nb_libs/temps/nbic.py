"""
实现一个 icecream包ic函数那样的，自动拼接  变量名1:变量值1,变量名2:变量值2 那样的字符串


例如
 a  =1
 b = 2

print(nbicf(a,b,
            a+b))

nbicf需要返回 a:1,b:2,a+b:3


"""

import inspect
import linecache
import functools
import re
import time


@functools.lru_cache(maxsize=10000)
def _parse_nbicf_call(filename, lineno):
    """
    快速解析nbicf调用的参数表达式
    """
    # 向上最多搜索5行找到nbicf调用
    for i in range(max(1, lineno - 4), lineno + 1):
        line = linecache.getline(filename, i)
        if 'nbicf(' in line:
            start_line = i
            break
    else:
        return None

    # 收集从nbicf(开始到)结束的所有代码
    code_lines = []
    paren_count = 0
    found_start = False

    for line_num in range(start_line, lineno + 5):
        line = linecache.getline(filename, line_num)
        if not line:
            break

        if not found_start:
            # 找到nbicf(的位置
            nbicf_pos = line.find('nbicf(')
            if nbicf_pos >= 0:
                found_start = True
                line = line[nbicf_pos + 6:]  # 从nbicf(后开始

        if found_start:
            for char in line:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    if paren_count == 0:
                        # 找到匹配的结束括号
                        code_lines.append(line[:line.index(char)])
                        # 简单的参数分割：用正则处理顶层逗号 
                        full_args = ''.join(code_lines)
                        # 移除多余空格但保持结构
                        full_args = re.sub(r'\s+', ' ', full_args.strip())
                        # 简单分割（不处理嵌套括号内的逗号）
                        args = [arg.strip() for arg in full_args.split(',') if arg.strip()]
                        return args
                    else:
                        paren_count -= 1
            code_lines.append(line)

    return None


def nbicf(*args):
    """
    Like icecream.ic(), but returns string instead of printing.
    """
    try:
        frame = inspect.currentframe().f_back
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno

        # 快速解析
        exprs = _parse_nbicf_call(filename, lineno)
        if not exprs or len(exprs) != len(args):
            # 解析失败，使用简单fallback
            exprs = ['?'] * len(args)

    except Exception:
        exprs = ['?'] * len(args)

    return ', '.join(f'{expr}: {value!r}' for expr, value in zip(exprs, args))


if __name__ == '__main__':
    import nb_print

    a = 1
    b = 2
    c = 3
    t1 = time.time()
    # c = a +b
    print()
    for i in range(10000):
        r = nbicf(a, b,
                  a + b)

        # r = (a,b,
        #         a+b)
        if i % 1000 == 0:
            print(r)
    print()

    # print(nbicf(a,c))

    print(time.time() - t1)
