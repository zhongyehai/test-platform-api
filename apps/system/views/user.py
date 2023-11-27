# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import system_manage
from ..model_factory import User
from ..forms.user import CreateUserForm, EditUserForm, ChangePasswordForm, LoginForm, GetUserListForm, \
    GetUserForm, DeleteUserForm, ChangeStatusUserForm
from ...enums import DataStatusEnum


@system_manage.login_get("/user/list")
def system_manage_get_user_list():
    """ 用户列表 """
    form = GetUserListForm()
    if form.detail:  # 获取用户详情列表
        get_filed = [User.id, User.name, User.account, User.status, User.create_time]
    else:
        get_filed = User.get_simple_filed_list()
    return app.restful.get_success(User.make_pagination(form, get_filed=get_filed))


@system_manage.permission_get("/user/role")
def system_manage_get_user_role_list():
    """ 获取用户的角色 """
    form = GetUserForm()
    return app.restful.get_success(form.user.roles)


@system_manage.post("/user/login")
def system_manage_login():
    """ 登录 """
    form = LoginForm()
    user_info = form.user.to_dict()
    user_permissions = form.user.get_permissions()
    user_info["token"] = form.user.make_token(user_permissions["api_addr_list"])
    user_info["front_permissions"] = user_permissions["front_addr_list"]
    return app.restful.login_success(user_info)


@system_manage.get("/user/logout")
def system_manage_logout():
    """ 登出 """
    return app.restful.logout_success()


@system_manage.login_put("/user/password")
def system_manage_change_password():
    """ 修改密码 """
    form = ChangePasswordForm()
    form.user.model_update({"password": form.new_password})
    return app.restful.change_success()


@system_manage.permission_put("/user/status")
def system_manage_change_status():
    """ 改变用户状态 """
    user = ChangeStatusUserForm().user
    user.disable() if user.status == DataStatusEnum.ENABLE.value else user.enable()
    return app.restful.change_success()


@system_manage.permission_get("/user")
def system_manage_get_user():
    """ 获取用户 """
    form = GetUserForm()
    return app.restful.get_success({"account": form.user.account, "name": form.user.name, "role_id": form.user.role_id})


@system_manage.permission_post("/user")
def system_manage_add_user():
    """ 新增用户 """
    form = CreateUserForm()
    for user_dict in form.user_list:
        role_list = user_dict.pop("role_list")
        user = User.model_create_and_get(user_dict)
        user.insert_user_roles(role_list)
    return app.restful.add_success()


@system_manage.permission_put("/user")
def system_manage_change_user():
    """ 修改用户 """
    form = EditUserForm()
    # if form.password is None:
    #     delattr(form, "password")
    form.user.model_update(form.model_dump())
    form.user.update_user_roles(form.role_list)
    return app.restful.change_success()


@system_manage.permission_delete("/user")
def system_manage_delete_user():
    """ 删除用户 """
    form = DeleteUserForm()
    form.user.delete()
    return app.restful.delete_success()
