import datetime

import orjson
import json
import pickle


class MyClass:
      def __init__(self, x, y):
            self.x = x
            self.y = y

      def __repr__(self):
            return f"MyClass(x={self.x}, y={self.y})"


d1 = {'t1':datetime.datetime.now(),
      't2':datetime.datetime.today(),
      "a":"哈哈",
      "b":"ok",
      "c":"cvalue",
      "obja":MyClass(1,2),
      }



print(d1)
print(pickle.dumps(d1))
# print(orjson.dumps(d1))
# print(orjson.loads(orjson.dumps(d1)))
# print(json.dumps(d1))
# print(json.loads(json.dumps(d1)))