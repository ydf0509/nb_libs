import inspect
import sys


def get_current_fun_name():
    """
    获取代码所在函数或方法的名字
    :return:
    """
    method_name = inspect.getframeinfo(inspect.currentframe().f_back).function  # 也可以 sys._getframe(0).f_code.co_name
    return method_name


class EasyFrame:
    def __init__(self, frame_level=0):
        self.framex = sys._getframe(frame_level + 1)  # 因为这里封装调用了一次,所以 +1

    @property
    def filename(self):
        return self.framex.f_code.co_filename

    @property
    def func_name(self):
        return self.framex.f_code.co_name

    @property
    def lineno(self):
        return self.framex.f_lineno

    def get_jump_line(self, next_line=False):
        next_line_str = ''
        if next_line:
            next_line_str = '\n'
        return f'''{next_line_str}"{self.filename}:{self.lineno}"'''


if __name__ == '__main__':
    from nb_log import print_raw


    def get_a():
        print(dir(sys._getframe(1).f_code))
        print(sys._getframe(1).f_code.co_filename)  # 文件
        print(sys._getframe(1).f_code.co_name)  # 函数
        print(sys._getframe(0).f_code.co_name)  # 函数
        print(dir(sys._getframe(1)))
        print(sys._getframe(1).f_lineno)  # 行
        print(sys._getframe(0).f_back.f_lineno)

        ef = EasyFrame(0)
        print(ef.filename, ef.lineno, ef.func_name, ef.get_jump_line(next_line=True))

        ef = EasyFrame(1)
        print(ef.filename, ef.lineno, ef.func_name, ef.get_jump_line(next_line=True))


    get_a()
