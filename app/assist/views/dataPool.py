# -*- coding: utf-8 -*-
from flask import current_app as app, request
from app.assist.blueprint import assist
from app.assist.forms.dataPool import GetDataPoolForm, PutDataPoolForm, DeleteDataPoolForm, PostDataPoolForm
from app.baseView import LoginRequiredView
from app.assist.models.dataPool import AutoTestUser, DataPool


class GetAutoTestUserListView(LoginRequiredView):

    def get(self):
        """ 获取自动化测试用户数据列表 """
        user_list = AutoTestUser.get_all(env=request.args.get("env"))
        return app.restful.success("获取成功", data=[
            auto_user.to_dict(pop_list=["created_time", "update_time"]) for auto_user in user_list
        ])


class GetDataPoolListView(LoginRequiredView):

    def get(self):
        """ 获取数据池列表 """
        form = GetDataPoolForm().do_validate()
        return app.restful.success("获取成功", DataPool.make_pagination(form))


class GetDataPoolBusinessStatusListView(LoginRequiredView):

    def get(self):
        """ 获取数据池业务状态 """
        data_list = DataPool.query.with_entities(DataPool.business_status).distinct().all()
        return app.restful.success("获取成功", [data[0] for data in data_list])


class GetDataPoolUseStatusListView(LoginRequiredView):

    def get(self):
        """ 获取数据池使用状态 """
        return app.restful.success("获取成功", {"not_used": "未使用", "in_use": "使用中", "used": "已使用"})


class DataPoolView(LoginRequiredView):

    def get(self):
        """ 获取数据池数据 """
        return app.restful.success("获取成功", DataPool.get_first(id=request.args.get("id")).to_dict())

    def post(self):
        """ 新增数据池数据 """
        form = PostDataPoolForm().do_validate()
        data_pool = DataPool().create(form.data)
        return app.restful.success("新增成功", data_pool.to_dict())

    def put(self):
        """ 修改数据池数据 """
        form = PutDataPoolForm().do_validate()
        form.data_pool.update(form.data)
        return app.restful.success("修改成功", form.data_pool.to_dict())

    def delete(self):
        """ 删除数据池数据 """
        form = DeleteDataPoolForm().do_validate()
        form.data_pool.delete()
        return app.restful.success("删除成功")


assist.add_url_rule("/autoTestUser", view_func=GetAutoTestUserListView.as_view("GetAutoTestUserListView"))
assist.add_url_rule("/dataPool", view_func=DataPoolView.as_view("DataPoolView"))
assist.add_url_rule("/dataPool/list", view_func=GetDataPoolListView.as_view("GetDataPoolListView"))
assist.add_url_rule("/dataPool/useStatus",
                    view_func=GetDataPoolUseStatusListView.as_view("GetDataPoolUseStatusListView"))
assist.add_url_rule("/dataPool/businessStatus",
                    view_func=GetDataPoolBusinessStatusListView.as_view("GetDataPoolBusinessStatusListView"))
