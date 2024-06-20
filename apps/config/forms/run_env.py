# -*- coding: utf-8 -*-
import re
from typing import Optional, List

from pydantic import Field, field_validator

from ..model_factory import RunEnv, BusinessLine
from ...base_form import BaseForm, PaginationForm, required_str_field, pydanticBaseModel


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


class RunEnvForm(pydanticBaseModel):
    """ 环境表单校验 """
    name: str = required_str_field(title="环境名")
    code: str = required_str_field(title="环境code")
    group: str = required_str_field(title="环境分组")
    desc: Optional[str] = Field(None, title="备注")


class PostRunEnvForm(BaseForm):
    """ 新增环境表单校验 """
    env_list: List[RunEnvForm] = Field(..., title="环境list")

    @field_validator("env_list")
    def validate_env_list(cls, value):
        code_list = []
        for env in value:
            if env.code in code_list:
                raise ValueError(f"环境code【{env.code}】重复")
            if re.match('^[a-zA-Z][a-zA-Z0-9_\\.]+$', env.code) is None:
                raise ValueError(f"环境code【{env.code}】错误，正确格式为：英文字母开头+英文字母/下划线/数字")
            code_list.append(env.code)

        run_env = RunEnv.db.session.query(RunEnv.code).filter(RunEnv.code.in_(code_list)).first()
        cls.validate_is_false(run_env, f"环境code{run_env}已存在")
        return value


class PutRunEnvForm(GetRunEnvForm, RunEnvForm):
    """ 修改环境表单校验 """

    @field_validator("code")
    def validate_code(cls, value):
        if re.match('^[a-zA-Z][a-zA-Z0-9_\\.]+$', value) is None:
            raise ValueError(f"环境code【{value}】错误，正确格式为：英文字母开头+英文字母/下划线/数字")
        return value


class GetEnvGroupForm(BaseForm):
    """ 获取环境分组 """
    env_list: list = required_str_field(title="环境")
    business_list: list = required_str_field(title="业务线")
    command: str = required_str_field(title="操作类型")  # add、delete


class EnvToBusinessForm(BaseForm):
    """ 批量管理环境与业务线的关系 绑定/解除绑定 """
    env_list: list = required_str_field(title="环境")
    business_list: list = required_str_field(title="业务线")
    command: str = required_str_field(title="操作类型")  # add、delete
