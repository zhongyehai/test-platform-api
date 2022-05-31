#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm
from flask_login import login_user, logout_user, current_user

from app.utils import restful
from app.utils.required import admin_required, login_required, generate_reset_token
from app.ucenter import ucenter
from app.baseView import AdminMethodView
from app.baseModel import db
from .models import User, Role
from .forms import (CreateUserForm, EditUserForm, ChangePasswordForm, LoginForm, FindUserForm, GetUserEditForm,
                    DeleteUserForm, ChangeStatusUserForm)


@ucenter.route('/role/list', methods=['GET'])
@login_required
def role_list():
    """ 角色列表 """
    return restful.success(data=[{'id': role.id, 'name': role.name} for role in Role.get_all()])


@ucenter.route('/list', methods=['GET'])
@login_required
def user_list():
    """ 用户列表 """
    form = FindUserForm()
    if form.validate():
        return restful.success(data=User.make_pagination(form))
    return restful.fail(form.get_error())


@ucenter.route('/login', methods=['POST'])
def login():
    """ 登录 """
    form = LoginForm()
    if form.validate():
        user = form.user
        login_user(user, remember=True)
        user_info, token = user.to_dict(), generate_reset_token(user)
        user_info['token'] = token
        return restful.success('登录成功', user_info)
    return restful.fail(msg=form.get_error())


@ucenter.route('/logout', methods=['GET'])
# @login_required
def logout():
    """ 登出 """
    logout_user()
    return restful.success(msg='登出成功')


@ucenter.route('/password', methods=['PUT'])
@login_required
def user_password():
    """ 修改密码 """
    form = ChangePasswordForm()
    if form.validate():
        with db.auto_commit():
            current_user.password = form.newPassword.data
        return restful.success(f'密码已修改为 {form.newPassword.data}')
    return restful.fail(msg=form.get_error())


@ucenter.route('/status', methods=['PUT'])
@admin_required
@login_required
def user_status():
    """ 改变用户状态 """
    form = ChangeStatusUserForm()
    if form.validate():
        user = form.user
        with db.auto_commit():
            user.status = 0 if user.status == 1 else 1
        return restful.success(f'{"禁用" if user.status == 0 else "启用"}成功')
    return restful.fail(form.get_error())


class UserView(AdminMethodView):
    """ 用户管理 """

    def get(self):
        form = GetUserEditForm()
        if form.validate():
            data = {'account': form.user.account, 'name': form.user.name, 'role_id': form.user.role_id}
            return restful.success(data=data)
        return restful.fail(form.get_error())

    def post(self):
        form = CreateUserForm()
        if form.validate():
            user = User().create(form.data)
            return restful.success(f'用户 {form.name.data} 新增成功', user.to_dict())
        return restful.fail(msg=form.get_error())

    def put(self):
        form = EditUserForm()
        if form.validate():
            form.password.data = form.password.data or form.user.password  # 若密码字段有值则修改密码，否则不修改密码
            form.user.update(form.data)
            return restful.success(f'用户 {form.user.name} 修改成功', form.user.to_dict())
        return restful.fail(msg=form.get_error())

    def delete(self):
        form = DeleteUserForm()
        if form.validate():
            form.user.delete()
            return restful.success('删除成功')
        return restful.fail(form.get_error())


ucenter.add_url_rule('/', view_func=UserView.as_view('user'))
