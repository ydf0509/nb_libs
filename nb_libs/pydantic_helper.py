import json
import typing
from collections import OrderedDict

from pydantic import BaseModel, BaseConfig

class BaseJsonAbleModel(BaseModel):
    """
    因为model字段包括了 函数和自定义类型的对象,无法直接json序列化,需要自定义json序列化
    """

    class Config(BaseConfig):
        arbitrary_types_allowed = True
        # allow_mutation = False
        extra = "forbid"
    def get_str_dict(self):
        model_dict: dict = self.dict()  # noqa
        model_dict_copy = OrderedDict()
        for k, v in model_dict.items():
            if isinstance(v, typing.Callable):
                model_dict_copy[k] = str(v)
            # elif k in ['specify_concurrent_pool', 'specify_async_loop'] and v is not None:
            elif type(v).__module__ != "builtins":  # 自定义类型的对象,json不可序列化,需要转化下.
                model_dict_copy[k] = str(v)
            else:
                model_dict_copy[k] = v
        return model_dict_copy

    def json_str_value(self):
        try:
            return json.dumps(self.get_str_dict(), ensure_ascii=False, )
        except TypeError as e:
            return str(self.get_str_dict())

    def json_pre(self):
        try:
            return json.dumps(self.get_str_dict(), ensure_ascii=False, indent=4)
        except TypeError as e:
            return str(self.get_str_dict())

    def update_from_dict(self, dictx: dict,is_generate_new_model=False,is_ignore_field_not_exists=False):
        model = self
        if is_generate_new_model:
            model = self.copy()
        for k, v in dictx.items():
            if is_ignore_field_not_exists is True:
                if k in model.dict():
                    setattr(model, k, v)
            else:
                setattr(model, k, v)
        return model

    def update_from_kwargs(self,is_generate_new_model=False,is_ignore_field_not_exists=False, **kwargs,):
        model = self
        # print(id(model))
        if is_generate_new_model:
            model = self.copy()
            # print(id(model))
        for k, v in kwargs.items():
            if is_ignore_field_not_exists is True:
                if k in model.dict():
                    setattr(model, k, v)
            else:
                setattr(model, k, v)
        return model

    def update_from_model(self, modelx: BaseModel,is_generate_new_model=False,is_ignore_field_not_exists=False):
        model = self
        if is_generate_new_model:
            model = self.copy()
        for k, v in modelx.dict().items():
            if is_ignore_field_not_exists is True:
                if k in model.dict():
                    setattr(model, k, v)
            else:
                setattr(model, k, v)
        return model

    def __str__(self):
        str1 =  self.__repr_str__(' ')
        return f'<{self.__class__.__name__} id:{id(self)} [{str1}]>'



if __name__ == '__main__':
    import nb_log


    class Model1(BaseJsonAbleModel):
        a:int=1
        c:int=66

    class Model2(BaseJsonAbleModel):
        a:int=2
        b:str = 'abcd'


    m1 = Model1(a=1)
    m2 = Model2(a=22)
    m1.update_from_model(m2,is_ignore_field_not_exists=True)
    print(m1)

    m1.update_from_dict(m2.dict(), is_ignore_field_not_exists=True)
    print(m1)

    m1_new = m1.update_from_kwargs(**m2.dict(), is_ignore_field_not_exists=True,is_generate_new_model=True)
    print(m1_new)

