# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.system.blueprint import system_manage
from app.system.forms.permission import FindPermissionForm, GetPermissionForm, CreatePermissionForm, \
    DeletePermissionForm, EditPermissionForm
from app.system.models.user import Permission


@system_manage.admin_get("/permission/type")
def system_manage_get_permission_type():
    """ 权限类型 """
    return app.restful.success(data={"api": '接口地址', "front": '前端地址'})


@system_manage.admin_get("/permission/list")
def system_manage_get_permission_list():
    """ 权限列表 """
    form = FindPermissionForm().do_validate()
    return app.restful.success(data=Permission.make_pagination(form))


@system_manage.admin_put("/permission/sort")
def system_manage_change_permission_sort():
    """ 修改排序 """
    Permission.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
    return app.restful.success(msg="修改排序成功")


@system_manage.admin_get("/permission")
def system_manage_get_permission():
    """ 获取权限 """
    form = GetPermissionForm().do_validate()
    return app.restful.success(data=form.permission.to_dict())


@system_manage.admin_post("/permission")
def system_manage_add_permission():
    """ 新增权限 """
    form = CreatePermissionForm().do_validate()
    form.num.data = Permission.get_insert_num()
    permission = Permission().create(form.data)
    return app.restful.success(f'权限 {form.name.data} 新增成功', permission.to_dict())


@system_manage.admin_put("/permission")
def system_manage_change_permission():
    """ 修改权限 """
    form = EditPermissionForm().do_validate()
    form.permission.update(form.data)
    return app.restful.success(f'权限 {form.permission.name} 修改成功', form.permission.to_dict())


@system_manage.admin_delete("/permission")
def system_manage_delete_permission():
    """ 删除权限 """
    form = DeletePermissionForm().do_validate()
    form.permission.delete()
    return app.restful.success("删除成功")
