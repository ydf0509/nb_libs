import json

import nb_log

from nb_libs.dict2json import dict2json

logger = nb_log.get_logger(__name__)


class GlobalDict:
    global_dict = {}

    @classmethod
    def show(cls):
        json_str = dict2json(cls.global_dict)
        logger.info(json_str)
        return json_str

    @classmethod
    def set(cls, k, v):
        cls.global_dict[k] = v

    @classmethod
    def get(cls, k, default=None):
        return cls.global_dict.get(k, default=default)


