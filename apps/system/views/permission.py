# -*- coding: utf-8 -*-
from flask import current_app as app

from ...base_form import ChangeSortForm
from ..blueprint import system_manage
from ..forms.permission import GetPermissionListForm, GetPermissionForm, CreatePermissionForm, \
    DeletePermissionForm, EditPermissionForm
from ..model_factory import Permission


@system_manage.admin_get("/permission/type")
def system_manage_get_permission_type():
    """ 权限类型 """
    return app.restful.get_success({"api": '接口地址', "front": '前端地址'})


@system_manage.admin_get("/permission/list")
def system_manage_get_permission_list():
    """ 权限列表 """
    form = GetPermissionListForm()
    if form.detail:
        get_filed = [Permission.id, Permission.source_type, Permission.name, Permission.source_addr, Permission.desc,
                     Permission.create_time]
    else:
        get_filed = [Permission.id, Permission.name, Permission.source_type]
    return app.restful.get_success(Permission.make_pagination(form, get_filed=get_filed))


@system_manage.admin_put("/permission/sort")
def system_manage_change_permission_sort():
    """ 修改排序 """
    form = ChangeSortForm()
    Permission.change_sort(**form.model_dump())
    return app.restful.change_success()


@system_manage.admin_get("/permission")
def system_manage_get_permission():
    """ 获取权限 """
    form = GetPermissionForm()
    return app.restful.get_success(form.permission.to_dict())


@system_manage.admin_post("/permission")
def system_manage_add_permission():
    """ 新增权限 """
    form = CreatePermissionForm()
    Permission.model_batch_create([permission.model_dump() for permission in form.data_list])
    return app.restful.add_success()


@system_manage.admin_put("/permission")
def system_manage_change_permission():
    """ 修改权限 """
    form = EditPermissionForm()
    form.permission.model_update(form.model_dump())
    return app.restful.change_success()


@system_manage.admin_delete("/permission")
def system_manage_delete_permission():
    """ 删除权限 """
    form = DeletePermissionForm()
    Permission.delete_by_id(form.id)
    return app.restful.delete_success()
