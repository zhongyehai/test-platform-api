# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import Field, field_validator

from ..model_factory import RunEnv, BusinessLine
from ...base_form import BaseForm, PaginationForm


class GetRunEnvListForm(PaginationForm):
    """ 获取环境列表 """
    name: Optional[str] = Field(None, title="环境名")
    code: Optional[str] = Field(None, title="环境code")
    group: Optional[str] = Field(None, title="环境分组")
    create_user: Optional[str] = Field(None, title="创建者")
    business_id: Optional[int] = Field(None, title="业务线")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.business_id:
            env_id_list = BusinessLine.get_env_list(self.business_id)
            filter_list.append(RunEnv.id.in_(env_id_list))
        if self.name:
            filter_list.append(RunEnv.name.like(f'%{self.name}%'))
        if self.code:
            filter_list.append(RunEnv.code.like(f'%{self.code}%'))
        if self.group:
            filter_list.append(RunEnv.group.like(f'%{self.group}%'))
        if self.create_user:
            filter_list.append(RunEnv.create_user == self.create_user)
        return filter_list


class GetRunEnvForm(BaseForm):
    """ 获取环境表单校验 """
    id: int = Field(..., title="环境id")

    @field_validator("id")
    def validate_id(cls, value):
        run_env = cls.validate_data_is_exist("数据不存在", RunEnv, id=value)
        setattr(cls, "run_env", run_env)
        return value


class DeleteRunEnvForm(GetRunEnvForm):
    """ 删除环境表单校验 """


class PostRunEnvForm(BaseForm):
    """ 新增环境表单校验 """
    name: str = Field(..., title="环境名")
    code: str = Field(..., title="环境code")
    group: str = Field(..., title="环境分组")
    desc: Optional[str] = Field(None, title="备注")


class PutRunEnvForm(GetRunEnvForm, PostRunEnvForm):
    """ 修改环境表单校验 """


class GetEnvGroupForm(BaseForm):
    """ 获取环境分组 """
    env_list: list = Field(..., title="环境")
    business_list: list = Field(..., title="业务线")
    command: str = Field(..., title="操作类型")  # add、delete


class EnvToBusinessForm(BaseForm):
    """ 批量管理环境与业务线的关系 绑定/解除绑定 """
    env_list: list = Field(..., title="环境")
    business_list: list = Field(..., title="业务线")
    command: str = Field(..., title="操作类型")  # add、delete
