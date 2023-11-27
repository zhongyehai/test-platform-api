# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import Field, field_validator, ValidationInfo

from ...base_form import BaseForm, PaginationForm
from ..model_factory import BusinessLine
from ...enums import ReceiveTypeEnum, BusinessLineBindEnvTypeEnum
from ...system.model_factory import User


class GetBusinessListForm(PaginationForm):
    """ 获取业务线列表 """
    code: Optional[str] = Field(None, title="业务线code")
    name: Optional[str] = Field(None, title="业务线名")
    get_all: Optional[int] = Field(None, title="获取所有业务线，需管理员权限")
    create_user: Optional[str] = Field(None, title="创建者")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if User.is_not_admin():
            filter_list.append(BusinessLine.id.in_(User.get_current_business_list()))
        if self.name:
            filter_list.append(BusinessLine.name.like(f'%{self.name}%'))
        if self.code:
            filter_list.append(BusinessLine.code.like(f'%{self.code}%'))
        if self.create_user:
            filter_list.append([BusinessLine.create_user == self.create_user])
        return filter_list


class GetBusinessForm(BaseForm):
    """ 获取业务线表单校验 """
    id: int = Field(..., title="业务线id")

    @field_validator("id")
    def validate_id(cls, value):
        business = cls.validate_data_is_exist("数据不存在", BusinessLine, id=value)
        setattr(cls, "business", business)
        return value


class DeleteBusinessForm(GetBusinessForm):
    """ 删除业务线表单校验 """

    @field_validator("id")
    def validate_id(cls, value):
        user_name = User.db.session.query(User.name).filter(User.business_list.like(f'{value}')).first()
        cls.validate_is_false(user_name, f'业务线被用户【{user_name[0]}】引用，请先解除引用')
        return value


class PostBusinessForm(BaseForm):
    """ 新增业务线表单校验 """
    code: str = Field(..., title="业务线code")
    name: str = Field(..., title="业务线名")
    receive_type: ReceiveTypeEnum = Field(
        ..., title="接收通知类型", description="not_receive:不接收、we_chat:企业微信、ding_ding:钉钉")
    webhook_list: list = Field(..., title="接收通统计知的渠道")
    bind_env: BusinessLineBindEnvTypeEnum = Field(
        ..., title="绑定环境机制", description="auto：新增环境时自动绑定，human：新增环境后手动绑定")
    env_list: list = Field(..., title="业务线要用的环境")
    desc: Optional[str] = Field(title="备注")

    @field_validator("receive_type")
    def validate_receive_type(cls, value, info: ValidationInfo):
        if value != ReceiveTypeEnum.not_receive:
            cls.validate_is_true(f"要接收段统计通知，则通知地址必填", info.data.get("webhook_list"))
        return value.value

    @field_validator("bind_env")
    def validate_bind_env(cls, value):
        return value.value


class PutBusinessForm(GetBusinessForm, PostBusinessForm):
    """ 修改业务线表单校验 """


class BusinessToUserForm(BaseForm):
    """ 批量管理业务线与用户的关系 绑定/解除绑定 """
    business_list: list = Field(..., title="业务线")
    user_list: list = Field(..., title="用户")
    command: str = Field(..., title="操作类型")  # add、delete
