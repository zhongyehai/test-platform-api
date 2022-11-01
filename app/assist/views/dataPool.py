# -*- coding: utf-8 -*-

from flask import current_app as app, request
from app.assist.blueprint import assist
from app.baseView import LoginRequiredView
from app.assist.models.dataPool import AutoTestPolyFactoring, AutoTestUser


class GetDataPoolListView(LoginRequiredView):

    def get(self):
        """ 获取数据池数据列表 """
        return app.restful.success('获取成功', data=[
            data_pool.to_dict(pop_list=['created_time', 'update_time']) for data_pool in
            AutoTestPolyFactoring.query.filter().order_by(AutoTestPolyFactoring.id.desc()).all()
        ])


class GetAutoTestUserListView(LoginRequiredView):

    def get(self):
        """ 获取自动化测试用户数据列表 """
        return app.restful.success('获取成功', data=[
            auto_user.to_dict(pop_list=['created_time', 'update_time']) for auto_user in
            AutoTestUser.get_all(env=request.args.get('env', 'test'))
        ])


assist.add_url_rule('/assist/dataPool', view_func=GetDataPoolListView.as_view('GetDataPoolListView'))
assist.add_url_rule('/assist/autoTestUser', view_func=GetAutoTestUserListView.as_view('GetAutoTestUserListView'))
