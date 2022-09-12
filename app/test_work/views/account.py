# -*- coding: utf-8 -*-

from flask import current_app as app

from app.baseView import LoginRequiredView
from app.test_work import test_work
from app.test_work.forms.account import GetAccountListForm, GetAccountForm, DeleteAccountForm, AddAccountForm, \
    ChangeAccountForm
from app.test_work.models.account import AccountModel

ns = test_work.namespace("account", description="测试账号管理相关接口")


@ns.route('/item/list/')
class GetAccountItemListView(LoginRequiredView):

    def get(self):
        """ 获取账号项目列表、角色列表、权限列表 """
        project_list = AccountModel.query.with_entities(AccountModel.project).distinct().all()
        role_list = AccountModel.query.with_entities(AccountModel.role).distinct().all()
        permission_list = AccountModel.query.with_entities(AccountModel.permission).distinct().all()
        return app.restful.success(
            '获取成功',
            data={
                'project_list': [{'key': project[0], 'value': project[0]} for project in project_list],
                'role_list': [{'key': role[0], 'value': role[0]} for role in role_list],
                'permission_list': [{'key': permission[0], 'value': permission[0]} for permission in permission_list]
            })


@ns.route('/list/')
class GetAccountListView(LoginRequiredView):

    def get(self):
        """ 获取账号列表 """
        form = GetAccountListForm()
        return app.restful.success('获取成功', data=AccountModel.make_pagination(form.data))


@ns.route('/')
class AccountView(LoginRequiredView):
    """ 测试账号管理 """

    def get(self):
        """ 获取账号 """
        form = GetAccountForm()
        if form.validate():
            return app.restful.success('获取成功', data=form.account.to_dict())
        return app.restful.fail(form.get_error())

    def post(self):
        """ 新增账号 """
        form = AddAccountForm()
        if form.validate():
            account = AccountModel().create(form.data)
            return app.restful.success('新增成功', data=account.to_dict())
        return app.restful.fail(form.get_error())

    def put(self):
        """ 修改账号 """
        form = ChangeAccountForm()
        if form.validate():
            form.account.update(form.data)
            return app.restful.success('修改成功', data=form.account.to_dict())
        return app.restful.fail(form.get_error())

    def delete(self):
        """ 删除账号 """
        form = DeleteAccountForm()
        if form.validate():
            form.account.delete()
            return app.restful.success('删除成功')
        return app.restful.fail(form.get_error())
