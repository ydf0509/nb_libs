import datetime

import orjson
import json

d1 = {'t1':datetime.datetime.now(),
      't2':datetime.datetime.today(),
      }



print(d1)

print(orjson.dumps(d1))

print(json.dumps(d1))