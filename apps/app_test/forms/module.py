# -*- coding: utf-8 -*-
from typing import Optional, List

from pydantic import field_validator
from sqlalchemy import or_

from ...base_form import BaseForm, PaginationForm, Field, required_str_field
from ..model_factory import AppUiPage as Page, AppUiProject as Project, AppUiModule as Module


class GetModuleTreeForm(BaseForm):
    project_id: int = Field(..., title="APP id")


class GetModuleListForm(GetModuleTreeForm, PaginationForm):
    """ 查找模块 """
    name: Optional[str] = Field(None, title="模块名")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = [Module.project_id == self.project_id]
        if self.name:
            filter_list.append(Project.name.like(f'%{self.name}%'))
        return filter_list


class GetModuleForm(BaseForm):
    """ 获取模块信息 """
    id: int = Field(..., title="模块id")

    @classmethod
    def validate_module_is_exist(cls, value):
        """ 校验模块存在 """
        return cls.validate_data_is_exist("模块不存在", Module, id=value)

    @field_validator("id")
    def validate_id(cls, value):
        module = cls.validate_module_is_exist(value)
        setattr(cls, 'module', module)
        return value


class DeleteModuleForm(GetModuleForm):
    """ 删除模块 """

    @field_validator("id")
    def validate_id(cls, value):
        data = Module.db.session.query(
            Module.create_user).filter(or_(Page.module_id == value, Module.parent == value)).first()
        cls.validate_is_false(data, "请先删除当前模块下的子模块及模块下的页面")
        return value


class AddModuleForm(GetModuleTreeForm):
    """ 添加模块的校验 """
    data_list: List[str] = required_str_field(title="模块名list")
    parent: Optional[int] = Field(title="父级id")

    def depends_validate(self):
        module_list = [
            {"project_id": self.project_id, "parent": self.parent, "name": module_name}
            for module_name in self.data_list
        ]
        self.data_list = module_list


class EditModuleForm(GetModuleTreeForm, GetModuleForm):
    """ 修改模块的校验 """
    parent: Optional[int] = Field(title="父级id")
    name: str = required_str_field(title="模块名")
