from typing import Optional
from pydantic import Field, field_validator

from ...base_form import BaseForm, PaginationForm
from ..model_factory import ConfigType


class GetConfigTypeListForm(PaginationForm):
    """ 获取配置类型列表 """
    name: Optional[str] = Field(None, title="类型名")
    create_user: Optional[int] = Field(None, title="创建者")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.name:
            filter_list.append(ConfigType.name.like(f'%{self.name}%'))
        if self.create_user:
            filter_list.append(ConfigType.create_user == self.create_user)
        return filter_list


class GetConfigTypeForm(BaseForm):
    """ 配置类型id存在 """
    id: int = Field(..., title="配置类型id")

    @field_validator("id")
    def validate_id(cls, value):
        conf_type = cls.validate_data_is_exist("配置类型不存在", ConfigType, id=value)
        setattr(cls, "conf_type", conf_type)
        return value


class DeleteConfigTypeForm(GetConfigTypeForm):
    """ 删除配置类型表单校验 """


class PostConfigTypeForm(BaseForm):
    """ 新增配置类型表单校验 """
    name: str = Field(..., title="配置类型名")
    desc: Optional[str] = Field(title="备注")


class PutConfigTypeForm(GetConfigTypeForm, PostConfigTypeForm):
    """ 修改配置类型表单校验 """
