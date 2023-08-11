# -*- coding: utf-8 -*-
from flask import current_app as app

from app.baseView import AdminRequiredView, NotLoginView, LoginRequiredView, PermissionRequiredView
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


class GetUserListView(LoginRequiredView):

    def get(self):
        """ 用户列表 """
        form = FindUserForm().do_validate()
        if form.detail.data:  # 获取用户详情列表
            return app.restful.success(data=User.make_pagination(form))
        return app.restful.success(
            data={"data": [user.to_dict(filter_list=["id", "name"]) for user in User.get_all()]}
        )


class GetUserRoleListView(PermissionRequiredView):

    def get(self):
        """ 获取用户的角色 """
        form = GetUserForm().do_validate()
        return app.restful.success(data=form.user.roles)


class UserLoginView(NotLoginView):

    def post(self):
        """ 登录 """
        form = LoginForm().do_validate()
        user_info = form.user.to_dict()
        user_permissions = form.user.get_permissions()
        user_info["token"] = form.user.generate_reset_token(user_permissions["api_addr_list"])
        user_info["front_permissions"] = user_permissions["front_addr_list"]
        return app.restful.success("登录成功", user_info)


class UserLogoutView(NotLoginView):

    def get(self):
        """ 登出 """
        return app.restful.success(msg="登出成功")


class ChangeUserPasswordView(LoginRequiredView):

    def put(self):
        """ 修改密码 """
        form = ChangePasswordForm().do_validate()
        form.user.update({"password": form.newPassword.data})
        return app.restful.success(f'密码已修改为 {form.newPassword.data}')


class ChangeUserStatusView(PermissionRequiredView):

    def put(self):
        """ 改变用户状态 """
        user = ChangeStatusUserForm().do_validate().user
        user.disable() if user.status == 1 else user.enable()
        return app.restful.success(f'{"禁用" if user.status == 0 else "启用"}成功')


class UserView(PermissionRequiredView):
    """ 用户管理 """

    def get(self):
        """ 获取用户 """
        form = GetUserForm().do_validate()
        data = {"account": form.user.account, "name": form.user.name, "role_id": form.user.role_id}
        return app.restful.success(data=data)

    def post(self):
        """ 新增用户 """
        form = CreateUserForm().do_validate()
        for user_dict in form.user_list.data:
            user = User().create(user_dict)
            user.insert_user_roles(user_dict["role_list"])
        return app.restful.success(f'用户新增成功')

    def put(self):
        """ 修改用户 """
        form = EditUserForm().do_validate()
        if form.password.data is None:
            delattr(form, "password")
        form.user.update(form.data)
        form.user.update_user_roles(form.role_list.data)
        return app.restful.success(f'用户 {form.user.name} 修改成功', form.user.to_dict())

    # def delete(self):
    #     """ 删除用户 """
    #     form = DeleteUserForm()
    #     if form.validate():
    #         form.user.delete()
    #         return app.restful.success("删除成功")
    #     return app.restful.fail(form.get_error())


system_manage.add_url_rule("/user", view_func=UserView.as_view("UserView"))
system_manage.add_url_rule("/user/login", view_func=UserLoginView.as_view("UserLoginView"))
system_manage.add_url_rule("/user/logout", view_func=UserLogoutView.as_view("UserLogoutView"))
system_manage.add_url_rule("/user/list", view_func=GetUserListView.as_view("GetUserListView"))
system_manage.add_url_rule("/user/role", view_func=GetUserRoleListView.as_view("GetUserRoleListView"))
system_manage.add_url_rule("/user/status", view_func=ChangeUserStatusView.as_view("ChangeUserStatusView"))
system_manage.add_url_rule("/user/password", view_func=ChangeUserPasswordView.as_view("ChangeUserPasswordView"))
