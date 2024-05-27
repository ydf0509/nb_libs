from functools import partial
from typing import Union
import copy
from redis import Redis
from redis.typing import ExpiryT, AbsExpiryT, EncodableT, FieldT
from inspect import signature


def _get_locals_params(key_name, loclasx: dict):
    loc = copy.copy(loclasx)
    loc.pop('self')
    loc['name'] = key_name
    return loc


class RedisKeyOp:
    redis_methods = [attr for attr in dir(Redis) if callable(getattr(Redis, attr)) and not attr.startswith("__")]
    methods_name_op = []  # 第二个入参是name,第一个入参是self的Reids类的方法名大全
    for m in redis_methods:
        fun_param_name_list = list(signature(getattr(Redis, m)).parameters.keys())
        if len(fun_param_name_list) > 1 and fun_param_name_list[1] == 'name' and fun_param_name_list[0] == 'self':
            methods_name_op.append(m)

    def __init__(self, redis_conn: Redis, key: str):
        self.redis_conn = redis_conn
        self.key_name = key
        self.get = partial(self.redis_conn.get, self.key_name)

    def set(self, value: EncodableT,
            ex: Union[ExpiryT, None] = None,
            px: Union[ExpiryT, None] = None,
            nx: bool = False,
            xx: bool = False,
            keepttl: bool = False,
            get: bool = False,
            exat: Union[AbsExpiryT, None] = None,
            pxat: Union[AbsExpiryT, None] = None, ):
        params = _get_locals_params(self.key_name, locals())
        return self.redis_conn.set(**params)

    def lpush(self, *values: FieldT):
        return self.redis_conn.lpush(self.key_name, *values)

    def __getattr__(self, item: str):
        if item in self.methods_name_op:
            return partial(getattr(self.redis_conn, item), self.key_name)
        else:
            raise AttributeError(f'not support redis `name` method {item}')


if __name__ == '__main__':
    redis_conn = Redis(decode_responses=True, encoding='utf-8')
    print(RedisKeyOp.methods_name_op)
    ro_test_key = RedisKeyOp(redis_conn, 'test_key')
    ro_test_key.set(456)
    print(ro_test_key.get())

    RedisKeyOp(redis_conn, 'tk2').incr()
