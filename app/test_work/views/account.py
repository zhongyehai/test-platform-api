# -*- coding: utf-8 -*-

from flask import current_app as app, request, views

from app.test_work import test_work
from app.test_work.models.account import AccountModel


@test_work.route('/account/project/list')
def get_account_project_list():
    """ 获取账号项目列表 """
    project_list = AccountModel.query.with_entities(AccountModel.project).distinct().all()
    return app.restful.success('获取成功', data=[{'key': project[0], 'value': project[0]} for project in project_list])


@test_work.route('/account/list')
def get_account_list():
    """ 获取账号列表 """
    return app.restful.success('获取成功', data=AccountModel.make_pagination({
        'page_num': request.args.get('pageNum'),
        'page_size': request.args.get('pageSize'),
        'event': request.args.get('event'),
        'project': request.args.get('project'),
        'name': request.args.get('name')
    }))


class AccountView(views.MethodView):
    """ 测试账号管理 """

    def get(self):
        """ 获取用户信息 """
        return app.restful.success('获取成功', data=AccountModel.get_first(id=request.args.get('id')).to_dict())

    def post(self):
        """ 新增账号 """

        if AccountModel.get_first(
                project=request.json['project'],
                event=request.json['event'],
                account=request.json['account']):
            return app.restful.fail(f"当前环境下 {request.json['account']} 账号已存在，直接修改即可")
        account = AccountModel().create(request.json)
        return app.restful.success('新增成功', data=account.to_dict())

    def put(self):
        """ 修改账号 """
        # 账号不重复
        account = AccountModel.get_first(
            project=request.json['project'],
            event=request.json['event'],
            account=request.json['account'])
        if account and account.id != request.json.get('id'):
            return app.restful.fail(f'当前环境下账号 {account.account} 已存在', data=account.to_dict())

        old_account = AccountModel.get_first(id=request.json.get('id'))
        old_account.update(request.json)
        return app.restful.success('修改成功', data=old_account.to_dict())

    def delete(self):
        """ 删除账号 """
        AccountModel.get_first(id=request.json.get('id')).delete()
        return app.restful.success('删除成功')


test_work.add_url_rule('/account', view_func=AccountView.as_view('account'))
