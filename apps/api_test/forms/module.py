# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo
from sqlalchemy import or_

from ...base_form import BaseForm, PaginationForm, Field
from ..model_factory import ApiProject as Project, ApiModule as Module, ApiMsg as Api


class GetModuleTreeForm(BaseForm):
    project_id: int = Field(..., title="服务id")


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

    @field_validator("id")
    def validate_id(cls, value):
        module = cls.validate_data_is_exist("模块不存在", Module, id=value)
        setattr(cls, 'module', module)
        return value


class DeleteModuleForm(GetModuleForm):
    """ 删除模块 """

    @field_validator("id")
    def validate_id(cls, value):
        data = Module.db.session.query(
            Module.create_user).filter(or_(Api.module_id == value, Module.parent == value)).first()
        cls.validate_is_false(data, "请先删除当前模块下的子模块及模块下的页面")
        return value


class AddModuleForm(GetModuleTreeForm):
    """ 添加模块的校验 """
    parent: Optional[int] = Field(title="父级id")
    name: str = Field(..., title="模块名")

    @field_validator('name')
    def validate_name(cls, value, info: ValidationInfo):
        """ 模块名不重复 """
        project_id, parent = info.data["project_id"], info.data["parent"]
        cls.validate_data_is_not_exist(
            f"当前服务中已存在名为【{value}】的模块", Module, project_id=project_id, name=value, parent=parent
        )
        return value


class EditModuleForm(AddModuleForm, GetModuleForm):
    """ 修改模块的校验 """

    @field_validator('id', 'name')
    def validate_name(cls, value, info: ValidationInfo):
        """ 模块名不重复 """
        if info.field_name == 'id':
            module = cls.validate_data_is_exist("模块不存在", Module, id=value)
            setattr(cls, 'module', module)
        elif info.field_name == 'name':
            data_id, project_id, parent = info.data["id"], info.data["project_id"], info.data["parent"]
            cls.validate_data_is_not_repeat(
                f"当前服务中已存在名为【{value}】的模块",
                Module, data_id, project_id=project_id, name=value, parent=parent
            )
        return value
