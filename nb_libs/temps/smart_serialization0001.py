import typing
import json
import orjson
import pickle
import ast


class Serialization:
    @staticmethod
    def to_json_str(dic: typing.Union[dict, str]):
        if isinstance(dic, str):
            return dic
        str1 = orjson.dumps(dic)
        return str1.decode('utf8')

    @staticmethod
    def to_dict(strx: typing.Union[str, dict]):
        if isinstance(strx, dict):
            return strx
        return orjson.loads(strx)

    @staticmethod
    def find_can_not_json_serializable_keys(dic: dict) -> typing.List[str]:
        can_not_json_serializable_keys = []
        dic = Serialization.to_dict(dic)
        for k, v in dic.items():
            if not isinstance(v, str):
                try:
                    json.dumps(v)
                except:
                    can_not_json_serializable_keys.append(k)
        return can_not_json_serializable_keys


class PickleHelper:
    @staticmethod
    def to_str(obj_x: typing.Any):
        return str(pickle.dumps(obj_x))  # 对象pickle,转成字符串

    @staticmethod
    def to_obj(str_x: str):
        return pickle.loads(ast.literal_eval(str_x))  # 不是从字节转成对象,是从字符串转,所以需要这样.


class SmartSerialization:
    """智能宽松序列化类"""

    @staticmethod
    def serialize(obj: typing.Any) -> str:
        """
        智能序列化：优先使用JSON，无法序列化的部分使用pickle
        """
        if isinstance(obj, dict):
            # 创建一个副本用于处理
            processed_dict = {}
            for key, value in obj.items():
                try:
                    # 尝试直接JSON序列化该值
                    json.dumps(value)
                    processed_dict[key] = value
                except (TypeError, ValueError):
                    # 如果JSON序列化失败，使用pickle序列化
                    pickle_str = PickleHelper.to_str(value)
                    processed_dict[key] = {
                        "__pickle__": True,
                        "data": pickle_str
                    }

            # 序列化整个字典
            return Serialization.to_json_str(processed_dict)
        else:
            # 非字典对象直接尝试JSON序列化
            try:
                return Serialization.to_json_str(obj)
            except (TypeError, ValueError):
                return PickleHelper.to_str(obj)

    @staticmethod
    def deserialize(serialized_str: str) -> typing.Any:
        """
        智能反序列化：自动识别并处理pickle序列化的部分
        """
        try:
            # 先尝试作为JSON反序列化
            result = Serialization.to_dict(serialized_str)

            if isinstance(result, dict):
                # 检查是否有pickle序列化的数据
                processed_result = {}
                for key, value in result.items():
                    if isinstance(value, dict) and value.get("__pickle__") is True:
                        # 这是pickle序列化的数据，需要反序列化
                        pickle_data = value.get("data")
                        if pickle_data:
                            processed_result[key] = PickleHelper.to_obj(pickle_data)
                        else:
                            processed_result[key] = value
                    else:
                        processed_result[key] = value
                return processed_result
            else:
                return result
        except (json.JSONDecodeError, orjson.JSONDecodeError):
            # 如果JSON反序列化失败，尝试pickle反序列化
            return PickleHelper.to_obj(serialized_str)


# 使用示例
if __name__ == "__main__":
    # 测试数据
    import datetime

    test_dict = {
        "name": "张三",
        "age": 25,
        "scores": [90, 85, 92],
        "metadata": {"city": "北京", "active": True},
        "created_time": datetime.datetime.now(),  # 这个无法JSON序列化
        "complex_obj": {"nested": {"data": datetime.date.today()}}  # 嵌套的复杂对象
    }

    print("原始数据:")
    print(test_dict)
    print()

    # 智能序列化
    serialized = SmartSerialization.serialize(test_dict)
    print("序列化后的字符串:")
    print(serialized)
    print()

    # 智能反序列化
    deserialized = SmartSerialization.deserialize(serialized)
    print("反序列化后的数据:")
    print(deserialized)
    print()

    # 验证是否相等
    print("原始时间和反序列化时间是否相等:", test_dict["created_time"] == deserialized["created_time"])