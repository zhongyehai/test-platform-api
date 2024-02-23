from typing import Optional, List

from pydantic import field_validator

from ...base_form import BaseForm, PaginationForm, Field, required_str_field, AddAppiumServerDataForm, AddPhoneDataForm
from ..model_factory import AppUiRunServer as Server, AppUiRunPhone as Phone


class GetServerListForm(PaginationForm):
    """ 获取服务器列表 """
    name: Optional[str] = Field(None, title="服务器名")
    os: Optional[str] = Field(None, title="服务器系统类型")
    ip: Optional[str] = Field(None, title="服务器ip")
    port: Optional[str] = Field(None, title="服务器端口")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.name:
            filter_list.append(Server.name.like(f'%{self.name}%'))
        if self.os:
            filter_list.append(Server.os == self.os)
        if self.ip:
            filter_list.append(Server.ip == self.ip)
        if self.port:
            filter_list.append(Server.port == self.port)
        return filter_list


class GetServerForm(BaseForm):
    """ 校验服务器id已存在 """
    id: int = Field(..., title="服务器id")

    @field_validator("id")
    def validate_id(cls, value):
        """ 校验id存在 """
        server = cls.validate_data_is_exist("服务器不存在", Server, id=value)
        setattr(cls, "server", server)
        return value


class AddServerForm(BaseForm):
    """ 添加服务器的校验 """
    data_list: List[AddAppiumServerDataForm] = required_str_field("appium服务器")


class EditServerForm(GetServerForm, AddAppiumServerDataForm):
    """ 修改服务器的校验 """


class GetPhoneListForm(PaginationForm):
    """ 查找服务器信息 """
    name: Optional[str] = Field(None, title="运行设备名")
    os: Optional[str] = Field(None, title="运行设备系统类型")
    os_version: Optional[str] = Field(None, title="运行设备系统版本")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.name:
            filter_list.append(Phone.name.like(f'%{self.name}%'))
        if self.os:
            filter_list.append(Phone.os == self.os)
        if self.os_version:
            filter_list.append(Phone.os_version.like(f'%{self.os_version}%'))
        return filter_list


class GetPhoneForm(BaseForm):
    """ 校验手机id已存在 """
    id: int = Field(..., title="运行设备id")

    @field_validator("id")
    def validate_id(cls, value):
        """ 校验id存在 """
        phone = cls.validate_data_is_exist("设备不存在", Phone, id=value)
        setattr(cls, "phone", phone)
        return value


class AddPhoneForm(BaseForm):
    """ 添加手机的校验 """
    data_list: List[AddPhoneDataForm] = required_str_field("手机设备")


class EditPhoneForm(GetPhoneForm, AddPhoneDataForm):
    """ 修改手机的校验 """
