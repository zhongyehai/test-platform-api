# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.baseView import AdminRequiredView
from app.system.blueprint import system_manage
from app.system.forms.permission import FindPermissionForm, GetPermissionForm, CreatePermissionForm, \
    DeletePermissionForm, EditPermissionForm
from app.system.models.user import User, Permission


class GetPermissionTypeView(AdminRequiredView):

    def get(self):
        """ 权限类型 """
        return app.restful.success(data={"api": '接口地址', "front": '前端地址'})


class GetPermissionListView(AdminRequiredView):

    def get(self):
        """ 权限列表 """
        form = FindPermissionForm().do_validate()
        return app.restful.success(data=Permission.make_pagination(form))


class PermissionChangeSortView(AdminRequiredView):

    def put(self):
        """ 修改排序 """
        Permission.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class PermissionView(AdminRequiredView):
    """ 权限管理 """

    def get(self):
        """ 获取权限 """
        form = GetPermissionForm().do_validate()
        return app.restful.success(data=form.permission.to_dict())

    def post(self):
        """ 新增权限 """
        form = CreatePermissionForm().do_validate()
        form.num.data = Permission.get_insert_num()
        permission = Permission().create(form.data)
        return app.restful.success(f'权限 {form.name.data} 新增成功', permission.to_dict())

    def put(self):
        """ 修改权限 """
        form = EditPermissionForm().do_validate()
        form.permission.update(form.data)
        return app.restful.success(f'权限 {form.permission.name} 修改成功', form.permission.to_dict())

    def delete(self):
        """ 删除权限 """
        form = DeletePermissionForm().do_validate()
        form.permission.delete()
        return app.restful.success("删除成功")


system_manage.add_url_rule("/permission", view_func=PermissionView.as_view("PermissionView"))
system_manage.add_url_rule("/permission/type", view_func=GetPermissionTypeView.as_view("GetPermissionTypeView"))
system_manage.add_url_rule("/permission/list", view_func=GetPermissionListView.as_view("GetPermissionListView"))
system_manage.add_url_rule("/permission/sort", view_func=PermissionChangeSortView.as_view("PermissionChangeSortView"))
