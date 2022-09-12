# -*- coding: utf-8 -*-
from flask import current_app as app

from app.baseView import AdminRequiredView, NotLoginView, LoginRequiredView
from app.system import system_manage
from app.baseModel import db
from app.system.models.user import User
from app.system.forms.user import (
    CreateUserForm,
    EditUserForm,
    ChangePasswordForm,
    LoginForm,
    FindUserForm,
    GetUserEditForm,
    DeleteUserForm,
    ChangeStatusUserForm
)

ns = system_manage.namespace("user", description="用户管理相关接口")


@ns.route('/list/')
class GetUserListView(LoginRequiredView):

    def get(self):
        """ 用户列表 """
        form = FindUserForm()
        if form.validate():
            if form.detail.data:  # 获取用户详情列表
                return app.restful.success(data=User.make_pagination(form))
            return app.restful.success(
                data={"data": [user.to_dict(filter_list=['id', 'name']) for user in User.get_all()]})
        return app.restful.fail(form.get_error())


@ns.route('/login/')
class UserLoginView(NotLoginView):

    def post(self):
        """ 登录 """
        form = LoginForm()
        if form.validate():
            user = form.user
            user_info = user.to_dict()
            user_info['token'] = user.generate_reset_token()
            return app.restful.success('登录成功', user_info)
        return app.restful.fail(msg=form.get_error())


@ns.route('/logout/')
class UserLogoutView(NotLoginView):

    def get(self):
        """ 登出 """
        return app.restful.success(msg='登出成功')


@ns.route('/password/')
class ChangeUserPasswordView(AdminRequiredView):

    def put(self):
        """ 修改密码 """
        form = ChangePasswordForm()
        if form.validate():
            form.user.update({'password': form.newPassword.data})
            return app.restful.success(f'密码已修改为 {form.newPassword.data}')
        return app.restful.fail(msg=form.get_error())


@ns.route('/status/')
class ChangeUserStatusView(AdminRequiredView):

    def put(self):
        """ 改变用户状态 """
        form = ChangeStatusUserForm()
        if form.validate():
            user = form.user
            with db.auto_commit():
                user.status = 0 if user.status == 1 else 1
            return app.restful.success(f'{"禁用" if user.status == 0 else "启用"}成功')
        return app.restful.fail(form.get_error())


@ns.route('/')
class UserView(AdminRequiredView):
    """ 用户管理 """

    def get(self):
        """ 获取用户 """
        form = GetUserEditForm()
        if form.validate():
            data = {'account': form.user.account, 'name': form.user.name, 'role_id': form.user.role_id}
            return app.restful.success(data=data)
        return app.restful.fail(form.get_error())

    def post(self):
        """ 新增用户 """
        form = CreateUserForm()
        if form.validate():
            user = User().create(form.data)
            return app.restful.success(f'用户 {form.name.data} 新增成功', user.to_dict())
        return app.restful.fail(msg=form.get_error())

    def put(self):
        """ 修改用户 """
        form = EditUserForm()
        if form.validate():
            form.user.update(form.data)
            return app.restful.success(f'用户 {form.user.name} 修改成功', form.user.to_dict())
        return app.restful.fail(msg=form.get_error())

    def delete(self):
        """ 删除用户 """
        form = DeleteUserForm()
        if form.validate():
            form.user.delete()
            return app.restful.success('删除成功')
        return app.restful.fail(form.get_error())
