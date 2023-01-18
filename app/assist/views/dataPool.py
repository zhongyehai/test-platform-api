# -*- coding: utf-8 -*-
from flask import current_app as app, request
from app.assist.blueprint import assist
from app.baseView import LoginRequiredView
from app.assist.models.dataPool import AutoTestUser


class GetAutoTestUserListView(LoginRequiredView):

    def get(self):
        """ 获取自动化测试用户数据列表 """
        user_list = AutoTestUser.get_all(env=request.args.get("env"))
        return app.restful.success("获取成功", data=[
            auto_user.to_dict(pop_list=["created_time", "update_time"]) for auto_user in user_list
        ])


assist.add_url_rule("/autoTestUser", view_func=GetAutoTestUserListView.as_view("GetAutoTestUserListView"))
