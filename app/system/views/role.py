# -*- coding: utf-8 -*-
from flask import current_app as app

from app.baseView import AdminRequiredView
from app.system.blueprint import system_manage
from app.system.forms.role import FindRoleForm, GetRoleForm, CreateRoleForm, EditRoleForm, DeleteRoleForm
from app.system.models.user import Role, Permission


class GetRoleListView(AdminRequiredView):

    def get(self):
        """ 获取角色列表 """
        form = FindRoleForm().do_validate()
        return app.restful.success(data=Role.make_pagination(form))


class RoleView(AdminRequiredView):
    """ 角色管理 """

    def get(self):
        """ 获取角色信息和对应的权限 """
        form = GetRoleForm().do_validate()
        permissions = Permission.get_role_permissions(form.id.data)
        return app.restful.success(data={
            "data": form.role.to_dict(),
            "all_permissions": permissions["all_permissions"],
            "front_permission": permissions["front_permissions"],
            "api_permission": permissions["api_permissions"]
        })

    def post(self):
        """ 新增角色 """
        form = CreateRoleForm().do_validate()
        role = Role().create(form.data)
        role.insert_role_permissions([*form.front_permission.data, *form.api_permission.data])
        return app.restful.success(f'角色 {form.name.data} 新增成功', role.to_dict())

    def put(self):
        """ 修改角色 """
        form = EditRoleForm().do_validate()
        form.role.update(form.data)
        form.role.update_role_permissions([*form.front_permission.data, *form.api_permission.data])
        return app.restful.success(f'角色 {form.role.name} 修改成功', form.role.to_dict())

    def delete(self):
        """ 删除角色 """
        form = DeleteRoleForm().do_validate()
        form.role.delete_role_permissions()
        form.role.delete()
        return app.restful.success("删除成功")


system_manage.add_url_rule("/role", view_func=RoleView.as_view("RoleView"))
system_manage.add_url_rule("/role/list", view_func=GetRoleListView.as_view("GetRoleListView"))
