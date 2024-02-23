# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import Field, field_validator

from ...base_form import BaseForm, PaginationForm, required_str_field
from ..model_factory import Role, User, UserRoles, Permission, RolePermissions


class GetRoleListForm(PaginationForm):
    """ 查找角色参数校验 """
    name: Optional[str] = Field(None, title="角色名")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.name:
            filter_list.append(Role.name.like(f'%{self.name}%'))

        # 当前用户如果不是管理员权限，则只返回当前用户有的角色
        if User.is_not_admin():
            admin_permission = Permission.db.session.query(
                Permission.id).filter(Permission.source_addr == "admin").all()
            not_admin_roles = Role.query.with_entities(Role.id).filter(Role.id == RolePermissions.role_id).filter(
                RolePermissions.permission_id.notin_(admin_permission)).distinct().all()
            filter_list.append(Role.id.in_(not_admin_roles))

        return filter_list


class GetRoleForm(BaseForm):
    """ 获取具体角色 """
    id: int = Field(..., title="角色id")

    @field_validator("id")
    def validate_id(cls, value):
        role = cls.validate_data_is_exist("数据不存在", Role, id=value)
        setattr(cls, "role", role)
        return value


class DeleteRoleForm(GetRoleForm):
    """ 删除角色 """

    @field_validator("id")
    def validate_id(cls, value):
        """ 如果角色被角色使用了，则不能删除 """
        role = cls.validate_data_is_exist("数据不存在", Role, id=value)
        setattr(cls, "role", role)
        cls.validate_data_is_not_exist(f"角色已被用户引用，请先解除引用", UserRoles, role_id=value)
        return value


class CreateRoleForm(BaseForm):
    """ 创建角色的验证 """

    name: str = required_str_field(title="角色名")
    desc: Optional[str] = Field(None, title="备注")
    extend_role: list = Field([], title="继承角色")
    api_permission: list = Field([], title="后端权限")
    front_permission: list = Field([], title="前端权限")


class EditRoleForm(GetRoleForm, CreateRoleForm):
    """ 编辑角色的校验 """
