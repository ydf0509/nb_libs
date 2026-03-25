import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nb_libs.smart_serialization import SmartSerialization, PickleHelper
from datetime import datetime, date, time as dt_time, timedelta


class MyClass:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def __repr__(self):
        return f"MyClass(x={self.x}, y={self.y})"


def performance_test():
    test_dict = {
        "name": "张三",
        "age": 25,
        "scores": [90, 85, 92],
        "metadata": {"city": "北京", "active": True},
        "created_time": datetime.now(),
        "birth_date": date(1990, 5, 15),
        "work_time": dt_time(9, 30, 0),
        "duration": timedelta(hours=2, minutes=30),
        "complex_obj": {"nested": {"data": datetime.now()}},
        "tags": {"python", "programming", "AI"},
        "tuple_a": (1, "hello"),
        "nested_tuple": ("a", (1, 2), {"key": "value"}),
        "mixed_list": [1, "string", datetime.now(), [1, 2, 3]],
        "obj_a": MyClass(1, 2),
        "payload": b"\x00\x01\x02\x03",
    }

    # 简单数据测试
    simple_dict = {
        "name": "张三",
        "age": 25,
        "scores": [90, 85, 92],
        "metadata": {"city": "北京", "active": True}
    }

    # 测试优化后的SmartSerialization性能
    print("测试SmartSerialization性能（复杂数据）...")
    start_time = time.time()
    for i in range(10000):
        serialized = SmartSerialization.serialize(test_dict)
        deserialized = SmartSerialization.deserialize(serialized)
    smart_time = time.time() - start_time
    print(f"SmartSerialization 10000次耗时: {smart_time:.4f}秒")

    # 测试简单数据的性能
    print("\n测试SmartSerialization性能（简单数据）...")
    start_time = time.time()
    for i in range(10000):
        serialized = SmartSerialization.serialize(simple_dict)
        deserialized = SmartSerialization.deserialize(serialized)
    simple_smart_time = time.time() - start_time
    print(f"SmartSerialization简单数据 10000次耗时: {simple_smart_time:.4f}秒")

    # 测试直接pickle性能（复杂数据）
    print("\n测试直接pickle性能（复杂数据）...")
    start_time = time.time()
    for i in range(10000):
        serialized = PickleHelper.to_str(test_dict)
        deserialized = PickleHelper.to_obj(serialized)
    pickle_time = time.time() - start_time
    print(f"直接pickle 10000次耗时: {pickle_time:.4f}秒")

    # 测试直接pickle性能（简单数据）
    print("\n测试直接pickle性能（简单数据）...")
    start_time = time.time()
    for i in range(10000):
        serialized = PickleHelper.to_str(simple_dict)
        deserialized = PickleHelper.to_obj(serialized)
    simple_pickle_time = time.time() - start_time
    print(f"直接pickle简单数据 10000次耗时: {simple_pickle_time:.4f}秒")

    print(f"\n性能对比:")
    print(f"  复杂数据: SmartSerialization是直接pickle的 {smart_time/pickle_time:.2f} 倍")
    print(f"  简单数据: SmartSerialization是直接pickle的 {simple_smart_time/simple_pickle_time:.2f} 倍")
    
    # 验证数据一致性
    print("\n验证数据一致性...")
    deserialized = SmartSerialization.deserialize(SmartSerialization.serialize(test_dict))
    print(f"created_time 是否相等: {test_dict['created_time'] == deserialized['created_time']}")
    print(f"birth_date 是否相等: {test_dict['birth_date'] == deserialized['birth_date']}")
    print(f"tuple_a 是否相等: {test_dict['tuple_a'] == deserialized['tuple_a']}")
    print(f"set 是否相等: {test_dict['tags'] == deserialized['tags']}")
    print(f"bytes 是否相等: {test_dict['payload'] == deserialized['payload']}")


if __name__ == "__main__":
    performance_test()