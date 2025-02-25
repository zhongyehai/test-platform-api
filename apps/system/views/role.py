# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import system_manage
from ..forms.role import GetRoleListForm, GetRoleForm, CreateRoleForm, EditRoleForm, DeleteRoleForm
from ..model_factory import Role, Permission
from ...base_form import ChangeSortForm


@system_manage.permission_get("/role/list")
def system_manage_get_role_list():
    """ 获取角色列表 """
    form = GetRoleListForm()
    if form.detail:
        get_filed = [Role.id, Role.name, Role.desc, Role.create_time, Role.update_time]
    else:
        get_filed = Role.get_simple_filed_list()
    return app.restful.get_success(Role.make_pagination(form, get_filed=get_filed))


@system_manage.admin_put("/role/sort")
def system_manage_change_role_sort():
    """ 修改排序 """
    form = ChangeSortForm()
    Role.change_sort(**form.model_dump())
    return app.restful.change_success()


@system_manage.admin_get("/role")
def system_manage_get_role():
    """ 获取角色信息和对应的权限 """
    form = GetRoleForm()
    permissions = Permission.get_role_permissions(form.id)
    return app.restful.get_success({
        "data": form.role.to_dict(),
        "all_permissions": permissions["all_permissions"],
        "front_permission": permissions["front_permissions"],
        "api_permission": permissions["api_permissions"]
    })


@system_manage.admin_post("/role")
def system_manage_add_role():
    """ 新增角色 """
    request_data = CreateRoleForm().model_dump()
    front_permission, api_permission = request_data.pop("front_permission"), request_data.pop("api_permission")
    role = Role.model_create_and_get(request_data)
    role.insert_role_permissions([*front_permission, *api_permission])
    return app.restful.add_success()


@system_manage.admin_put("/role")
def system_manage_change_role():
    """ 修改角色 """
    form = EditRoleForm()
    form.role.model_update(form.model_dump())
    form.role.update_role_permissions([*form.front_permission, *form.api_permission])
    return app.restful.change_success()


@system_manage.admin_delete("/role")
def system_manage_delete_role():
    """ 删除角色 """
    form = DeleteRoleForm()
    form.role.delete_role_permissions()
    form.role.delete()
    return app.restful.delete_success()
