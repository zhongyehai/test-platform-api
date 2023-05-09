# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.baseView import LoginRequiredView, NotLoginView
from app.config.models.runEnv import RunEnv
from app.config.forms.runEnv import (
    GetRunEnvForm, DeleteRunEnvForm, PostRunEnvForm, PutRunEnvForm, GetRunEnvListForm, EnvToBusinessForm
)
from app.config.blueprint import config_blueprint


class GetRunEnvListView(NotLoginView):

    def get(self):
        form = GetRunEnvListForm().do_validate()
        return app.restful.success(data=RunEnv.make_pagination(form))


class GeRunEnvGroupListView(LoginRequiredView):

    def get(self):
        """ 环境分组列表 """
        group_list = RunEnv.query.with_entities(RunEnv.group).distinct().all()
        return app.restful.success("获取成功", data=[group[0] for group in group_list])


class RunEnvChangeSortView(LoginRequiredView):

    def put(self):
        """ 修改排序 """
        RunEnv.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class EnvToBusiness(LoginRequiredView):
    """ 运行环境与业务线的绑定关系 """

    def put(self):
        form = EnvToBusinessForm().do_validate()
        RunEnv.env_to_business(form.env_list.data, form.business_list.data, form.command.data)
        return app.restful.success("修改成功")


class RunEnvView(LoginRequiredView):

    def get(self):
        """ 获取域名 """
        form = GetRunEnvForm().do_validate()
        return app.restful.success("获取成功", data=form.conf.to_dict())

    def post(self):
        """ 新增域名 """
        form = PostRunEnvForm().do_validate()
        form.num.data = RunEnv.get_insert_num()
        run_env = RunEnv().create(form.data)
        return app.restful.success("新增成功", data=run_env.to_dict())

    def put(self):
        """ 修改域名 """
        form = PutRunEnvForm().do_validate()
        form.run_env.update(form.data)
        return app.restful.success("修改成功", data=form.run_env.to_dict())

    def delete(self):
        """ 删除域名 """
        form = DeleteRunEnvForm().do_validate()
        form.run_env.delete()
        return app.restful.success("删除成功")


config_blueprint.add_url_rule("/runEnv", view_func=RunEnvView.as_view("RunEnvView"))
config_blueprint.add_url_rule("/runEnv/toBusiness", view_func=EnvToBusiness.as_view("EnvToBusiness"))
config_blueprint.add_url_rule("/runEnv/list", view_func=GetRunEnvListView.as_view("GetRunEnvListView"))
config_blueprint.add_url_rule("/runEnv/sort", view_func=RunEnvChangeSortView.as_view("RunEnvChangeSortView"))
config_blueprint.add_url_rule("/runEnv/group", view_func=GeRunEnvGroupListView.as_view("GeRunEnvGroupListView"))
