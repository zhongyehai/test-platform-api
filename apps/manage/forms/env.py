from typing import Optional, List

from pydantic import Field, field_validator

from ...base_form import BaseForm, PaginationForm, AddEnvDataForm, AddEnvAccountDataForm, required_str_field
from ..models.env import Env


class GetEnvListForm(PaginationForm):
    """ 获取数据列表 """
    business_list: Optional[str] = Field(None, title="业务线")
    name: Optional[str] = Field(None, title="环境名")
    value: Optional[str] = Field(None, title="数据值")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = [Env.source_type == 'addr']
        if self.name:
            filter_list.append(Env.name.like(f'%{self.name}%'))
        if self.value:
            filter_list.append(Env.value.like(f'%{self.value}%'))
        if self.business_list:
            filter_list.append(Env.business.in_(self.business_list.split(',')))

        return filter_list


class GetEnvForm(BaseForm):
    """ 数据详情 """
    id: int = Field(..., title="bug数据id")

    @field_validator("id")
    def validate_id(cls, value):
        env = cls.validate_data_is_exist("数据不存在", Env, id=value)
        setattr(cls, "env", env)
        return value


class DeleteEnvForm(GetEnvForm):
    """ 删除数据 """


class AddEnvForm(BaseForm):
    """ 添加数据 """
    business: Optional[int] = Field(..., title="业务线")
    data_list: List[AddEnvDataForm] = required_str_field(title="资源数据")

    def depends_validate(self):
        env_data_list = []
        for index, data in enumerate(self.data_list):
            data = data.model_dump()
            data["source_type"], data["business"] = 'addr', self.business
            env_data_list.append(data)
        self.data_list = env_data_list


class ChangeEnvForm(GetEnvForm):
    """ 修改数据 """
    business: Optional[int] = Field(title="业务线")
    name: str = required_str_field(title="资源名字")
    value: str = required_str_field(title="资源对应的值")
    desc: Optional[str] = Field(title="描述")


class GetAccountListForm(PaginationForm):
    """ 获取数据列表 """
    business: Optional[list] = Field(None, title="业务线")
    name: Optional[str] = Field(None, title="环境名")
    parent_id: int = Field(..., title="所属资源id")
    value: Optional[str] = Field(None, title="数据值")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = [Env.parent == self.parent_id, Env.source_type == 'account']
        if self.name:
            filter_list.append(Env.name.like(f'%{self.name}%'))
        if self.value:
            filter_list.append(Env.value.like(f'%{self.value}%'))
        if self.business:
            filter_list.append(Env.business == self.business)

        return filter_list


class GetAccountForm(BaseForm):
    """ 数据详情 """
    id: int = Field(..., title="bug数据id")

    @field_validator("id")
    def validate_id(cls, value):
        env = cls.validate_data_is_exist("数据不存在", Env, id=value)
        setattr(cls, "env", env)
        return value


class DeleteAccountForm(GetEnvForm):
    """ 删除数据 """


class AddAccountForm(BaseForm):
    """ 添加数据 """
    parent: Optional[int] = Field(None, title="数据父级id")
    data_list: List[AddEnvAccountDataForm] = required_str_field(title="资源数据")

    def depends_validate(self):
        env_data_list = []
        for index, data in enumerate(self.data_list):
            data = data.model_dump()
            data["source_type"], data["parent"] = 'account', self.parent
            env_data_list.append(data)
        self.data_list = env_data_list


class ChangeAccountForm(GetEnvForm):
    """ 修改数据 """
    name: str = required_str_field(title="资源名字")
    value: str = required_str_field(title="资源对应的值")
    password: Optional[str] = Field(None, title="密码")
    desc: Optional[str] = Field(None, title="描述")
