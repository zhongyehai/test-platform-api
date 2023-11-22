# -*- coding: utf-8 -*-
from typing import Optional
from pydantic import Field, field_validator

from ...base_form import BaseForm, PaginationForm
from ..model_factory import Permission, RolePermissions


class GetPermissionListForm(PaginationForm):
    """ 查找权限参数校验 """
    name: Optional[str] = Field(None, title="权限名")
    source_addr: Optional[str] = Field(None, title="权限地址")
    source_type: Optional[str] = Field(None, title="权限类型")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.name:
            filter_list.append(Permission.name.like(f'%{self.name}%'))
        if self.source_addr:
            filter_list.append(Permission.source_addr.like(f'%{self.source_addr}%'))
        if self.source_type:
            filter_list.append(Permission.source_type == self.source_type)
        return filter_list


class GetPermissionForm(BaseForm):
    """ 获取具体权限 """
    id: int = Field(..., title="权限id")

    @field_validator("id")
    def validate_id(cls, value):
        permission = cls.validate_data_is_exist("数据不存在", Permission, id=value)
        setattr(cls, "permission", permission)
        return value


class DeletePermissionForm(GetPermissionForm):
    """ 删除权限 """

    @field_validator("id")
    def validate_id(cls, value):
        cls.validate_data_is_not_exist("权限已被角色引用，请先解除引用", RolePermissions, permission_id=value)
        return value


class CreatePermissionForm(BaseForm):
    """ 创建权限的验证 """
    name: str = Field(..., title="权限名")
    desc: Optional[str] = Field(title="备注")
    source_addr: str = Field(..., title="权限地址")
    source_type: str = Field("front", title="权限类型")
    source_class: str = Field("menu", title="权限分类")

    def validate_name(self, field):
        """ 权限名不重复 """
        self.validate_data_is_not_exist(f"权限名 {field.data} 已存在", Permission, name=field.data)


class EditPermissionForm(GetPermissionForm, CreatePermissionForm):
    """ 编辑权限的校验 """
