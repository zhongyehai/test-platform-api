# -*- coding: utf-8 -*-
from flask import current_app as app

from app.system.blueprint import system_manage
from app.system.models.user import User
from app.system.forms.user import (
    CreateUserForm,
    EditUserForm,
    ChangePasswordForm,
    LoginForm,
    FindUserForm,
    GetUserForm,
    DeleteUserForm,
    ChangeStatusUserForm
)


@system_manage.login_get("/user/list")
def system_manage_get_user_list():
    """ 用户列表 """
    form = FindUserForm().do_validate()
    if form.detail.data:  # 获取用户详情列表
        return app.restful.success(data=User.make_pagination(form))
    return app.restful.success(
        data={"data": [user.to_dict(filter_list=["id", "name"]) for user in User.get_all()]}
    )


@system_manage.permission_get("/user/role")
def system_manage_get_user_role_list():
    """ 获取用户的角色 """
    form = GetUserForm().do_validate()
    return app.restful.success(data=form.user.roles)


@system_manage.post("/user/login")
def system_manage_login():
    """ 登录 """
    form = LoginForm().do_validate()
    user_info = form.user.to_dict()
    user_permissions = form.user.get_permissions()
    user_info["token"] = form.user.generate_reset_token(user_permissions["api_addr_list"])
    user_info["front_permissions"] = user_permissions["front_addr_list"]
    return app.restful.success("登录成功", user_info)


@system_manage.get("/user/logout")
def system_manage_logout():
    """ 登出 """
    return app.restful.success(msg="登出成功")


@system_manage.login_put("/user/password")
def system_manage_change_password():
    """ 修改密码 """
    form = ChangePasswordForm().do_validate()
    form.user.update({"password": form.newPassword.data})
    return app.restful.success(f'密码已修改为 {form.newPassword.data}')


@system_manage.permission_put("/user/status")
def system_manage_change_status():
    """ 改变用户状态 """
    user = ChangeStatusUserForm().do_validate().user
    user.disable() if user.status == 1 else user.enable()
    return app.restful.success(f'{"禁用" if user.status == 0 else "启用"}成功')


@system_manage.permission_get("/user")
def system_manage_get_user():
    """ 获取用户 """
    form = GetUserForm().do_validate()
    data = {"account": form.user.account, "name": form.user.name, "role_id": form.user.role_id}
    return app.restful.success(data=data)


@system_manage.permission_post("/user")
def system_manage_add_user():
    """ 新增用户 """
    form = CreateUserForm().do_validate()
    for user_dict in form.user_list.data:
        user = User().create(user_dict)
        user.insert_user_roles(user_dict["role_list"])
    return app.restful.success(f'用户新增成功')


@system_manage.permission_put("/user")
def system_manage_change_user():
    """ 修改用户 """
    form = EditUserForm().do_validate()
    if form.password.data is None:
        delattr(form, "password")
    form.user.update(form.data)
    form.user.update_user_roles(form.role_list.data)
    return app.restful.success(f'用户 {form.user.name} 修改成功', form.user.to_dict())


@system_manage.permission_delete("/user")
def system_manage_delete_user():
    """ 删除用户 """
    form = DeleteUserForm()
    if form.validate():
        form.user.delete()
        return app.restful.success("删除成功")
    return app.restful.fail(form.get_error())
