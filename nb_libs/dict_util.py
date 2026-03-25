import json
from datetime import date, datetime
from decimal import Decimal

def dict_to_loose_json(dictx: dict, indent=4):
    """宽松的json,使对象能被json序列化"""
    dict_new = {}
    for k, v in dictx.items():
        if isinstance(v, (bool, tuple, dict, float, int)):
            dict_new[k] = v
        else:
            dict_new[k] = str(v)
    return json.dumps(dict_new, ensure_ascii=False, indent=indent)


class EnhancedJSONEncoder(json.JSONEncoder):
    """
    一个可以处理 datetime, date, Decimal 等非标准JSON类型的编码器。
    return json.dumps(data, cls=EnhancedJSONEncoder)
    """
    def default(self, o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)


def dict_time_to_json(data):
    return json.dumps(data, cls=EnhancedJSONEncoder)




class Undefined:
    """表示未定义的值"""
    pass

def deep_get(d, keys, default=Undefined):
    """安全地获取嵌套字典的值。keys可以是 'a.b.c' 或 ['a', 'b', 'c']。"""
    if isinstance(keys, str):
        keys = keys.split('.')
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key)
        else:
            return default
    return d