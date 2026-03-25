import typing
import orjson
import pickle
import base64
from datetime import datetime, date, time, timedelta
import json as std_json


class Serialization:
    """高性能 JSON 封装：orjson 为主"""
    @staticmethod
    def to_json_str(obj: typing.Any) -> str:
        return orjson.dumps(obj).decode('utf8')

    @staticmethod
    def to_dict(data: str) -> dict:
        return orjson.loads(data)


class PickleHelper:
    """pickle <-> base64 文本化，安全且可放入 JSON"""
    @staticmethod
    def to_str(obj: typing.Any) -> str:
        return base64.b64encode(
            pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        ).decode('utf8')

    @staticmethod
    def to_obj(data: str) -> typing.Any:
        return pickle.loads(base64.b64decode(data))


"""
SmartSerialization 是一个智能序列化类,使用orjson序列化 + pickle 序列化
例如一个字典 {"a":1,"b":2,"c":3,"d":MyCalss(1,2)}
这个字典不能josn序列化,如果直接 pickle序列化,导致 a  b c 这种简单类型也看不清楚键值对,

SmartSerialization 是对不能json序列化的,使用pickle序列化,避免了 a b c 也看不清楚


注意这个源码的实现:
orjson 不同于 json,orjson能直接序列化各种时间对象成字符串,这会导致反序列化时候生成不了时间对象,
所以对时间对象类型需要改成pickle序列化,而不能使用orjson的序列化方式
"""
class SmartSerialization:
    TYPE_KEY = "__type__"
    DATA_KEY = "__data__"
    STR_KEY = "__str__"

    _CONTAINER_MAP = {"list": list, "tuple": tuple, "set": set}
    _DATETIME_TYPES = (datetime, date, time, timedelta)
    
    # 优化: 为反序列化器按类型名称预先计算映射
    _type_handlers: dict = {}
    _deserializers_by_name: dict = {}

    _simple_types = (str, int, float, bool, type(None))
    _simple_types_set = set(_simple_types)

    @classmethod
    def register_type(cls, py_type, serializer, deserializer):
        cls._type_handlers[py_type] = (serializer, deserializer)
        # 优化: 构建从类型名称到反序列化器的映射,以加快查找速度
        cls._deserializers_by_name[py_type.__name__] = deserializer

    @staticmethod
    def _process_for_serialization(obj: typing.Any) -> typing.Any:
        obj_type = type(obj)
        
        # 快速路径: 简单类型直接返回
        if obj_type in SmartSerialization._simple_types_set:
            return obj

        # 字典和列表非常常见,优先处理
        if obj_type is dict:
            # 优化: 仅当字典包含非简单类型时才进行处理
            if any(type(v) not in SmartSerialization._simple_types_set for v in obj.values()):
                process_func = SmartSerialization._process_for_serialization
                return {k: process_func(v) for k, v in obj.items()}
            return obj

        if obj_type is list:
            # 优化: 仅当列表包含非简单类型时才进行处理
            if any(type(item) not in SmartSerialization._simple_types_set for item in obj):
                process_func = SmartSerialization._process_for_serialization
                return [process_func(item) for item in obj]
            return obj

        # 检查已注册的自定义类型(为性能起见,进行精确匹配)
        if obj_type in SmartSerialization._type_handlers:
            ser, _ = SmartSerialization._type_handlers[obj_type]
            return {
                SmartSerialization.TYPE_KEY: obj_type.__name__,
                SmartSerialization.STR_KEY: str(obj),
                SmartSerialization.DATA_KEY: ser(obj)
            }

        # 元组和集合不是原生JSON类型,需要特殊处理
        if obj_type in (tuple, set):
            container_type = obj_type.__name__
            # 优化: 避免对只包含简单类型的容器进行递归
            if any(type(item) not in SmartSerialization._simple_types_set for item in obj):
                process_func = SmartSerialization._process_for_serialization
                processed_items = [process_func(item) for item in obj]
            else:
                processed_items = list(obj)
            return {
                SmartSerialization.TYPE_KEY: container_type,
                SmartSerialization.STR_KEY: str(obj),
                SmartSerialization.DATA_KEY: processed_items
            }

        # 日期时间类型被pickle以保留类型信息,因为orjson会将其字符串化
        if isinstance(obj, SmartSerialization._DATETIME_TYPES):
            return {
                SmartSerialization.TYPE_KEY: obj_type.__name__,
                SmartSerialization.STR_KEY: str(obj),  # 额外保存可读的时间字符串
                SmartSerialization.DATA_KEY: PickleHelper.to_str(obj)
            }

        # 后备: pickle任何其他复杂类型
        return {
            SmartSerialization.TYPE_KEY: "pickle",
            SmartSerialization.STR_KEY: str(obj),
            SmartSerialization.DATA_KEY: PickleHelper.to_str(obj)
        }

    @staticmethod
    def _process_for_deserialization(obj: typing.Any) -> typing.Any:
        obj_type = type(obj)
        
        # 快速路径: 简单类型直接返回
        if obj_type in SmartSerialization._simple_types_set:
            return obj

        if obj_type is dict:
            # 检查它是否是一个特殊序列化的对象
            if SmartSerialization.TYPE_KEY in obj:
                tname = obj[SmartSerialization.TYPE_KEY]
                data = obj.get(SmartSerialization.DATA_KEY)

                # 优化: 为已注册类型和容器进行直接查找
                deserializer = SmartSerialization._deserializers_by_name.get(tname)
                if deserializer:
                    return deserializer(data)

                if tname in SmartSerialization._CONTAINER_MAP:
                    deserialze_func = SmartSerialization._process_for_deserialization
                    iterable = [deserialze_func(i) for i in data]
                    return SmartSerialization._CONTAINER_MAP[tname](iterable)

                # 日期时间类型和通用的pickle后备
                if tname in ("datetime", "date", "time", "timedelta", "pickle"):
                    return PickleHelper.to_obj(data)

                return obj

            # 处理一个普通的字典
            if any(type(v) not in SmartSerialization._simple_types_set for v in obj.values()):
                deserialize_func = SmartSerialization._process_for_deserialization
                return {k: deserialize_func(v) for k, v in obj.items()}
            return obj

        if obj_type is list:
            deserialize_func = SmartSerialization._process_for_deserialization
            if any(type(item) not in SmartSerialization._simple_types_set for item in obj):
                return [deserialize_func(item) for item in obj]
            return obj

        return obj

    @staticmethod
    def serialize(obj: typing.Any) -> str:
        processed = SmartSerialization._process_for_serialization(obj)
        return Serialization.to_json_str(processed)

    @staticmethod
    def deserialize(data: str) -> typing.Any:
        try:
            obj = Serialization.to_dict(data)
            return SmartSerialization._process_for_deserialization(obj)
        except (orjson.JSONDecodeError, std_json.JSONDecodeError):
            # 非 JSON 文本时，尝试直接按 base64(pickle) 反序列化
            return PickleHelper.to_obj(data)

 # 可插拔类型示例（演示：将 bytes 注册为 base64 文本）
def bytes_serializer(b: bytes) -> str:
    return base64.b64encode(b).decode("utf8")

def bytes_deserializer(s: str) -> bytes:
    return base64.b64decode(s)

SmartSerialization.register_type(bytes, bytes_serializer, bytes_deserializer) # bytes类型现在会被新方法注册


# =========================
# 使用示例与一致性校验
# =========================
if __name__ == "__main__":
    class MyClass:
        def __init__(self, x, y):
            self.x = x
            self.y = y
        def __repr__(self):
            return f"MyClass(x={self.x}, y={self.y})"



    test_dict = {
        "name": "张三",
        "age": 25,
        "scores": [90, 85, 92],
        "metadata": {"city": "北京", "active": True},
        "created_time": datetime.now(),                     # datetime 对象
        "birth_date": date(1990, 5, 15),                    # date 对象
        "work_time": time(9, 30, 0),                        # time 对象
        "duration": timedelta(hours=2, minutes=30),         # timedelta 对象
        "complex_obj": {"nested": {"data": datetime.now()}},
        "tags": {"python", "programming", "AI"},            # set
        "tuple_a": (1, "hello"),                            # tuple
        "nested_tuple": ("a", (1, 2), {"key": "value"}),    # 嵌套 tuple
        "mixed_list": [1, "string", datetime.now(), [1, 2, 3]],
        "obj_a": MyClass(1, 2),                             # 自定义对象 → pickle
        "payload": b"\x00\x01\x02\x03",                     # bytes → 注册类型
    }

    print("原始数据:")
    for k, v in test_dict.items():
        print(f"  {k}: {v} ({type(v).__name__})")
    print()

    serialized = SmartSerialization.serialize(test_dict)
    print("序列化后的字符串:")
    print(serialized)
    print()

    deserialized = SmartSerialization.deserialize(serialized)
    print("反序列化后的数据:")
    for k, v in deserialized.items():
        print(f"  {k}: {v} ({type(v).__name__})")
    print()

    print("验证结果:")
    print(f"created_time 是否相等: {test_dict['created_time'] == deserialized['created_time']}")
    print(f"birth_date 是否相等: {test_dict['birth_date'] == deserialized['birth_date']}")
    print(f"tuple_a 是否相等: {test_dict['tuple_a'] == deserialized['tuple_a']}")
    print(f"tuple_a 反序列化类型: {type(deserialized['tuple_a']).__name__}")
    print(f"nested_tuple 是否相等: {test_dict['nested_tuple'] == deserialized['nested_tuple']}")
    print(f"nested_tuple 反序列化类型: {type(deserialized['nested_tuple']).__name__}")
    print(f"set 是否相等: {test_dict['tags'] == deserialized['tags']}")
    print(f"bytes 是否相等: {test_dict['payload'] == deserialized['payload']}")

    # 智能序列化,测试性能
    import  time as time_std
    t1 = time_std.time()
    for i in range(100000):
        str1 = SmartSerialization.serialize(test_dict)
        dic1 = SmartSerialization.deserialize(str1)
    print("智能序列化,100000次耗时: ",time_std.time() - t1)

    # pickle 粗暴序列化,测试性能
    t1 = time_std.time()
    for i in range(100000):
        str1 = PickleHelper.to_str(test_dict)
        dic1 =  PickleHelper.to_obj(str1)
    print("pickle粗暴 序列化,100000次耗时: ", time_std.time() - t1)