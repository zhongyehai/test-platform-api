# -*- coding: utf-8 -*-
from typing import Optional, List

from pydantic import Field, field_validator

from ..model_factory import WebHook
from ...base_form import BaseForm, PaginationForm, required_str_field, pydanticBaseModel
from ...enums import WebHookTypeEnum


class GetWebHookListForm(PaginationForm):
    """ 获取webhook列表 """
    name: Optional[str] = Field(None, title="webhook名字")
    addr: Optional[str] = Field(None, title="webhook地址")
    webhook_type: Optional[str] = Field(None, title="webhook类型")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.name:
            filter_list.append(WebHook.name.like(f'%{self.name}%'))
        if self.addr:
            filter_list.append(WebHook.addr.like(f'%{self.addr}%'))
        if self.webhook_type:
            filter_list.append(WebHook.webhook_type == self.webhook_type)
        return filter_list


class GetWebHookForm(BaseForm):
    """ 获取webhook校验 """
    id: int = Field(..., title="数据id")

    @field_validator("id")
    def validate_id(cls, value):
        webhook = cls.validate_data_is_exist("数据不存在", WebHook, id=value)
        setattr(cls, "webhook", webhook)
        return value


class DeleteWebHookForm(GetWebHookForm):
    """ 删除webhook校验 """


class WebHookForm(pydanticBaseModel):
    """ webhook校验 """
    name: str = required_str_field(title="webhook名字")
    addr: str = required_str_field(title="webhook地址")
    webhook_type: WebHookTypeEnum = required_str_field(title="webhook类型，钉钉、企业微信、飞书")
    secret: Optional[str] = Field(None, title="webhook秘钥")
    desc: Optional[str] = Field(None, title="备注")


class PostWebHookForm(BaseForm):
    """ 新增webhook校验 """
    data_list: List[WebHookForm] = Field(..., title="webhook list")


class PutWebHookForm(GetWebHookForm, WebHookForm):
    """ 修改webhook校验 """
