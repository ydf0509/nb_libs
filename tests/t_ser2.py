import time

import json
import orjson
str1 = '''


{
  "data": {
    "users": [
      {
        "id": 1,
        "name": "Alice Smith",
        "email": "alice.smith@example.com",
        "address": {
          "street": "123 Main St",
          "city": "Springfield",
          "state": "IL",
          "zip": "62704",
          "coordinates": {
            "latitude": 39.7817,
            "longitude": -89.6501
          }
        },
        "phoneNumbers": [
          {
            "type": "home",
            "number": "555-123-4567"
          },
          {
            "type": "work",
            "number": "555-987-6543"
          }
        ],
        "roles": ["admin", "user"],
        "preferences": {
          "theme": "dark",
          "notifications": true,
          "language": "en-US"
        },
        "metadata": {
          "createdAt": "2023-01-15T08:30:00Z",
          "lastLogin": "2023-10-05T14:22:18Z",
          "loginCount": 142
        }
      },
      {
        "id": 2,
        "name": "Bob Johnson",
        "email": "bob.johnson@example.com",
        "address": {
          "street": "456 Oak Ave",
          "city": "Riverside",
          "state": "CA",
          "zip": "92507",
          "coordinates": {
            "latitude": 33.9806,
            "longitude": -117.3755
          }
        },
        "phoneNumbers": [
          {
            "type": "mobile",
            "number": "555-555-0123"
          }
        ],
        "roles": ["user"],
        "preferences": {
          "theme": "light",
          "notifications": false,
          "language": "en-GB"
        },
        "metadata": {
          "createdAt": "2023-03-22T11:15:33Z",
          "lastLogin": "2023-10-06T09:45:22Z",
          "loginCount": 87
        }
      }
    ],
    "products": [
      {
        "id": "P001",
        "name": "UltraBook Pro Laptop",
        "category": "electronics",
        "price": 1299.99,
        "specifications": {
          "processor": "Intel i7-1260P",
          "ram": "16GB DDR5",
          "storage": "1TB NVMe SSD",
          "display": "14-inch 2.8K OLED"
        },
        "inStock": true,
        "tags": ["laptop", "ultrabook", "business"]
      },
      {
        "id": "P002",
        "name": "Wireless Noise-Cancelling Headphones",
        "category": "audio",
        "price": 349.99,
        "specifications": {
          "batteryLife": "30 hours",
          "connectivity": "Bluetooth 5.2",
          "weight": "250g"
        },
        "inStock": false,
        "tags": ["headphones", "wireless", "audio"]
      }
    ],
    "orders": [
      {
        "orderId": "ORD-2023-1001",
        "userId": 1,
        "items": [
          {
            "productId": "P001",
            "quantity": 1,
            "unitPrice": 1299.99
          },
          {
            "productId": "P002",
            "quantity": 2,
            "unitPrice": 349.99
          }
        ],
        "totalAmount": 1999.97,
        "status": "delivered",
        "timeline": {
          "placed": "2023-09-10T10:30:00Z",
          "shipped": "2023-09-12T14:15:00Z",
          "delivered": "2023-09-15T09:45:00Z"
        }
      }
    ]
  },
  "metadata": {
    "generatedAt": "2023-10-06T12:00:00Z",
    "version": "1.2.0",
    "api": {
      "rateLimit": 1000,
      "maxPageSize": 100
    }
  }
}
'''


str1 = '''
{"a":1,"b":2,"c":3,"d":4,"e":5,"f":6,"g":7,"h":8,"i":9,"j":10,"k":11,"l":12,"m":13,"n":14,"o":15,"p":16,"q":17,"r":18,"s":19,"t":20,"u":21,"v":22,"w":23,"x":24,"y":25,"z":26}
'''

t1 = time.time()
for i in range(100000):
    d1 = orjson.loads(str1)
    str2 = orjson.dumps(d1).decode('utf8')
    # if i==0:
    #     print(d1)
    #     print(str2)
print(time.time() - t1)


t2 = time.time()
for i in range(100000):
    d1 = json.loads(str1)
    str2 = json.dumps(d1)
    # if i==0:
    #     print(d1)
    #     print(str2)
print(time.time() - t2)


from nb_libs.smart_serialization import SmartSerialization,PickleHelper

t3 = time.time()
for i in range(100000):
    d1 = SmartSerialization.deserialize(str1)
    str2 = SmartSerialization.serialize(d1)
    # if i==0:
    #     print(d1)
    #     print(str2)
print(time.time() - t3)


# t4 = time.time()
# for i in range(100000):
#     d1 = PickleHelper.to_obj(str1)
#     str2 = PickleHelper.to_str(d1)
#     # if i==0:
#     #     print(d1)
#     #     print(str2)
# print(time.time() - t4)