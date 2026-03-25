"""
Tortoise ORM + Pydantic 混合基类实现
类似 SQLModel 的使用体验，但基于 Tortoise ORM
"""

from typing import Any, Dict, Optional, Type, TypeVar, get_type_hints
from tortoise import Model as TortoiseModel
from tortoise.fields import Field as TortoiseField, IntField, CharField, TextField, BooleanField, DatetimeField
from pydantic import BaseModel, ConfigDict, Field as PydanticField, create_model
from datetime import datetime
import inspect


T = TypeVar("T", bound="TortoiseModel")


class TortoisePydanticModelMeta(type(TortoiseModel), type(BaseModel)):
    """
    元类，用于协调 Tortoise Model 和 Pydantic BaseModel 的元类冲突
    """
    
    def __new__(mcs, name: str, bases: tuple, namespace: dict, **kwargs):
        # 提取 table 参数
        table = kwargs.pop("table", False)
        
        # 如果不是基类本身，且 table=True，则创建 Tortoise 模型
        if table and name != "TortoiseModel" and name != "BaseModel":
            # 分离字段定义
            tortoise_fields = {}
            pydantic_fields = {}
            annotations = namespace.get("__annotations__", {})
            
            for field_name, field_type in annotations.items():
                if field_name.startswith("_"):
                    continue
                    
                field_value = namespace.get(field_name, ...)
                
                # 如果是 TortoiseField，保留给 Tortoise
                if isinstance(field_value, TortoiseField):
                    tortoise_fields[field_name] = field_value
                else:
                    # 否则自动转换为 Tortoise 字段
                    tortoise_field = mcs._convert_to_tortoise_field(field_name, field_type, field_value)
                    if tortoise_field:
                        tortoise_fields[field_name] = tortoise_field
                        namespace[field_name] = tortoise_field
            
            # 设置 Tortoise 表名
            if "Meta" not in namespace:
                namespace["Meta"] = type("Meta", (), {"table": name.lower()})
            elif not hasattr(namespace["Meta"], "table"):
                namespace["Meta"].table = name.lower()
            
            # 先创建 Tortoise Model
            namespace["_is_table"] = True
            cls = type(TortoiseModel).__new__(type(TortoiseModel), name, (TortoiseModel,), namespace)
            
            # 为类添加 Pydantic 相关功能
            cls._add_pydantic_support(cls)
            
            return cls
        else:
            # 不创建表，仅作为 Pydantic 模型使用
            namespace["_is_table"] = False
            if bases and bases[0].__name__ == "TortoiseModel":
                # 这是基类本身
                return type(TortoiseModel).__new__(type(TortoiseModel), name, bases, namespace)
            else:
                # 创建纯 Pydantic 模型
                return type(BaseModel).__new__(type(BaseModel), name, (BaseModel,), namespace)
    
    @staticmethod
    def _convert_to_tortoise_field(field_name: str, field_type: type, default_value: Any) -> Optional[TortoiseField]:
        """
        将 Python 类型注解转换为 Tortoise 字段
        """
        origin_type = field_type
        
        # 处理 Optional 类型
        is_optional = False
        if hasattr(field_type, "__origin__"):
            if field_type.__origin__ is type(None) or str(field_type).startswith("typing.Optional"):
                # 提取 Optional 中的实际类型
                args = getattr(field_type, "__args__", ())
                if args:
                    field_type = args[0]
                    is_optional = True
        
        # 处理 Union 类型（包括 Optional[X] = Union[X, None]）
        if hasattr(field_type, "__origin__") and str(field_type.__origin__) == "typing.Union":
            args = getattr(field_type, "__args__", ())
            # 找到非 None 的类型
            for arg in args:
                if arg is not type(None):
                    field_type = arg
                    is_optional = True
                    break
        
        # 主键处理
        if field_name == "id" and default_value is None:
            return IntField(pk=True, null=False)
        
        # 根据类型创建相应的 Tortoise 字段
        field_kwargs = {"null": is_optional or default_value is None}
        
        # 处理默认值
        if default_value is not ... and default_value is not None and not isinstance(default_value, TortoiseField):
            field_kwargs["default"] = default_value
        
        if field_type == int:
            return IntField(**field_kwargs)
        elif field_type == str:
            # 默认使用 CharField，长度 255
            return CharField(max_length=255, **field_kwargs)
        elif field_type == bool:
            return BooleanField(**field_kwargs)
        elif field_type == datetime:
            return DatetimeField(**field_kwargs)
        else:
            # 对于复杂类型，使用 TextField 存储 JSON
            return TextField(**field_kwargs)
        
        return None


class TortoiseModel(TortoiseModel, BaseModel, metaclass=TortoisePydanticModelMeta):
    """
    混合基类：既是 Tortoise ORM 模型，也是 Pydantic 模型
    
    使用方式：
    ```python
    class Hero(TortoiseModel, table=True):
        id: Optional[int] = None
        name: str
        secret_name: str
        age: Optional[int] = None
    ```
    
    - table=True: 创建数据库表（Tortoise ORM 模型）
    - table=False 或不指定: 仅作为 Pydantic 模型使用
    """
    
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
    )
    
    @classmethod
    def _add_pydantic_support(cls, model_cls: Type[T]) -> None:
        """为 Tortoise 模型添加 Pydantic 支持"""
        
        # 添加 from_orm 类方法（Pydantic v2 改名为 model_validate）
        @classmethod
        def model_validate(cls_inner, obj: Any) -> BaseModel:
            """从 ORM 对象创建 Pydantic 模型"""
            if isinstance(obj, dict):
                return cls_inner(**obj)
            
            # 从 Tortoise 模型实例提取数据
            data = {}
            for field_name in cls_inner._meta.fields:
                if hasattr(obj, field_name):
                    data[field_name] = getattr(obj, field_name)
            return cls_inner(**data)
        
        model_cls.model_validate = model_validate
        
        # 添加 dict() 方法以兼容 Pydantic
        def model_dump(self, **kwargs) -> Dict[str, Any]:
            """导出为字典"""
            result = {}
            for field_name in self._meta.fields:
                if hasattr(self, field_name):
                    result[field_name] = getattr(self, field_name)
            return result
        
        model_cls.model_dump = model_dump
        model_cls.dict = model_dump  # 兼容旧版本
    
    class Meta:
        abstract = True


# ==================== 使用示例 ====================

class Hero(TortoiseModel, table=True):
    """示例：英雄模型"""
    id: Optional[int] = None
    name: str
    secret_name: str
    age: Optional[int] = None
    
    class Meta:
        table = "heroes"


# 如果只需要 Pydantic 模型（不创建表）
class HeroResponse(TortoiseModel):
    """API 响应模型"""
    id: int
    name: str
    age: Optional[int] = None


# ==================== FastAPI 使用示例 ====================
"""
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

app = FastAPI()

# 注册 Tortoise ORM
register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["__main__"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

@app.post("/heroes/", response_model=Hero)
async def create_hero(hero: Hero):
    # hero 既可以作为 Pydantic 模型接收请求
    # 也可以直接作为 ORM 模型保存
    await hero.save()
    return hero

@app.get("/heroes/{hero_id}", response_model=Hero)
async def get_hero(hero_id: int):
    hero = await Hero.get(id=hero_id)
    # 直接返回 ORM 对象，FastAPI 会自动序列化
    return hero
"""