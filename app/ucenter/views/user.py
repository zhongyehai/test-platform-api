# -*- coding: utf-8 -*-
from flask import views, current_app as app

from app.ucenter import ucenter
from app.baseModel import db
from app.ucenter.models.user import User, Role
from app.ucenter.forms.user import (
    CreateUserForm,
    EditUserForm,
    ChangePasswordForm,
    LoginForm,
    FindUserForm,
    GetUserEditForm,
    DeleteUserForm,
    ChangeStatusUserForm
)


@ucenter.route('/role/list', methods=['GET'])
def role_list_is_admin_required():
    """ 角色列表 """
    return app.restful.success(data=[{'id': role.id, 'name': role.name} for role in Role.get_all()])


@ucenter.route('/list', methods=['GET'])
def user_list():
    """ 用户列表 """
    form = FindUserForm()
    if form.validate():
        if form.detail.data:  # 获取用户详情列表
            return app.restful.success(data=User.make_pagination(form))
        return app.restful.success(data={"data": [user.to_dict(filter_list=['id', 'name']) for user in User.get_all()]})
    return app.restful.fail(form.get_error())


@ucenter.route('/login', methods=['POST'])
def login_not_login_required():
    """ 登录 """
    form = LoginForm()
    if form.validate():
        user = form.user
        user_info = user.to_dict()
        user_info['token'] = user.generate_reset_token()
        return app.restful.success('登录成功', user_info)
    return app.restful.fail(msg=form.get_error())


@ucenter.route('/logout', methods=['GET'])
def logout_not_login_required():
    """ 登出 """
    return app.restful.success(msg='登出成功')


@ucenter.route('/password', methods=['PUT'])
def user_password():
    """ 修改密码 """
    form = ChangePasswordForm()
    if form.validate():
        form.user.update({'password': form.newPassword.data})
        return app.restful.success(f'密码已修改为 {form.newPassword.data}')
    return app.restful.fail(msg=form.get_error())


@ucenter.route('/status', methods=['PUT'])
def user_status_is_admin_required():
    """ 改变用户状态 """
    form = ChangeStatusUserForm()
    if form.validate():
        user = form.user
        with db.auto_commit():
            user.status = 0 if user.status == 1 else 1
        return app.restful.success(f'{"禁用" if user.status == 0 else "启用"}成功')
    return app.restful.fail(form.get_error())


class UserView(views.MethodView):
    """ 用户管理 """

    def get(self):
        form = GetUserEditForm()
        if form.validate():
            data = {'account': form.user.account, 'name': form.user.name, 'role_id': form.user.role_id}
            return app.restful.success(data=data)
        return app.restful.fail(form.get_error())

    def post(self):
        form = CreateUserForm()
        if form.validate():
            user = User().create(form.data)
            return app.restful.success(f'用户 {form.name.data} 新增成功', user.to_dict())
        return app.restful.fail(msg=form.get_error())

    def put(self):
        form = EditUserForm()
        if form.validate():
            form.password.data = form.password.data or form.user.password  # 若密码字段有值则修改密码，否则不修改密码
            form.user.update(form.data)
            return app.restful.success(f'用户 {form.user.name} 修改成功', form.user.to_dict())
        return app.restful.fail(msg=form.get_error())

    def delete(self):
        form = DeleteUserForm()
        if form.validate():
            form.user.delete()
            return app.restful.success('删除成功')
        return app.restful.fail(form.get_error())


ucenter.add_url_rule('/', view_func=UserView.as_view('user_is_admin_required'))
