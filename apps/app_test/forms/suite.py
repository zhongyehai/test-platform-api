# -*- coding: utf-8 -*-
from typing import Optional, List

from pydantic import field_validator
from sqlalchemy import or_

from ...base_form import BaseForm, PaginationForm, Field, required_str_field
from ..model_factory import AppUiCase as Case, AppUiCaseSuite as CaseSuite, AppUiRunPhone as Phone, \
    AppUiRunServer as Server
from ...enums import UiCaseSuiteTypeEnum


class GetCaseSuiteListForm(PaginationForm):
    """ 获取用例集list """
    name: Optional[str] = Field(None, title="用例集名")
    suite_type: Optional[str] = Field(None, title="用例集类型")
    project_id: int = Field(..., title="服务id")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = [CaseSuite.project_id == self.project_id]
        if self.suite_type:
            filter_list.append(CaseSuite.suite_type.in_(self.suite_type.split(',')))
        if self.name:
            filter_list.append(CaseSuite.name.like(f'%{self.name}%'))
        return filter_list


class GetCaseSuiteForm(BaseForm):
    """ 获取用例集信息 """
    id: int = Field(..., title="用例集id")

    @field_validator("id")
    def validate_id(cls, value):
        suite = cls.validate_data_is_exist("用例集不存在", CaseSuite, id=value)
        setattr(cls, 'suite', suite)
        return value


class DeleteCaseSuiteForm(GetCaseSuiteForm):
    """ 删除用例集 """

    @field_validator("id")
    def validate_id(cls, value):
        data = CaseSuite.db.session.query(
            CaseSuite.create_user).filter(or_(Case.suite_id == value, CaseSuite.parent == value)).first()
        cls.validate_is_false(data, "请先删除当前用例集的子用例集及用例集下的用例")
        return value


class AddCaseSuiteForm(BaseForm):
    """ 添加用例集的校验 """
    project_id: int = Field(..., title="app id")
    suite_type: UiCaseSuiteTypeEnum = Field(
        ..., title="用例集类型", description="base: 基础用例集，process: 流程用例集，make_data: 造数据用例集")
    parent: Optional[int] = Field(title="父用例集id")
    data_list: List[str] = required_str_field(title="用例集名称list")

    def depends_validate(self):
        suite_data_list = [{
            "project_id": self.project_id,
            "suite_type": self.suite_type,
            "parent": self.parent,
            "name": suite_name
        } for suite_name in self.data_list]
        self.data_list = suite_data_list


class EditCaseSuiteForm(GetCaseSuiteForm):
    """ 编辑用例集 """
    project_id: int = Field(..., title="服务id")
    suite_type: UiCaseSuiteTypeEnum = Field(
        ..., title="用例集类型", description="base: 基础用例集，process: 流程用例集，make_data: 造数据用例集")
    parent: Optional[int] = Field(title="父用例集id")
    name: str = required_str_field(title="用例集名称")

    def depends_validate(self):
        setattr(
            self, 'is_update_suite_type',
            True if self.parent is None and self.suite_type != getattr(self, 'suite').suite_type else False
        )


class RunCaseSuiteForm(GetCaseSuiteForm):
    """ 运行用例集 """
    is_async: int = Field(default=0, title="执行模式")
    env_list: list = Field(default=[], title="运行环境")
    no_reset: bool = Field(default=False, title="是否不重置手机")
    server_id: int = Field(..., title="执行服务器")
    phone_id: int = Field(..., title="执行手机")

    @field_validator('id')
    def validate_id(cls, value):
        suite = cls.validate_data_is_exist("用例集不存在", CaseSuite, id=value)
        cls.validate_data_is_exist("用例集下没有用例", Case, suite_id=value)
        setattr(cls, "suite", suite)
        return value

    @field_validator("server_id")
    def validate_server_id(cls, value):
        """ 校验服务id存在 """
        server = cls.validate_data_is_exist("服务器不存在", Server, id=value)
        cls.validate_appium_server_is_running(server.ip, server.port)
        setattr(cls, "server", server)
        return value

    @field_validator("phone_id")
    def validate_phone_id(cls, value):
        """ 校验手机id存在 """
        phone = cls.validate_data_is_exist("执行设备不存在", Phone, id=value)
        setattr(cls, "phone", phone)
        return value
