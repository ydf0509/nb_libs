import inspect

def get_current_fun_name():
    """
    获取代码所在函数或方法的名字
    :return:
    """
    method_name = inspect.getframeinfo(inspect.currentframe().f_back).function
    return method_name