# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.baseView import LoginRequiredView, NotLoginView
from app.config.models.config import Config
from app.config.forms.config import (
    GetConfigForm, DeleteConfigForm, PostConfigForm, PutConfigForm, GetConfigListForm
)
from app.config.blueprint import config_blueprint
from config import skip_if_type_mapping, skip_if_data_source_mapping
from utils.view.required import admin_required


class GetConfListView(LoginRequiredView):

    def get(self):
        form = GetConfigListForm().do_validate()
        return app.restful.success(data=Config.make_pagination(form))


class GetRunTestModelView(NotLoginView):

    def get(self):
        """ 获取执行模式 """
        return app.restful.success(data={0: "串行执行", 1: "并行执行"})


class GetSkipIfTypeView(NotLoginView):

    def get(self):
        """ 获取跳过条件类型 """
        return app.restful.success(data=skip_if_type_mapping)


class GetSkipIfDataSourceView(NotLoginView):

    def get(self):
        """ 获取跳过条件数据源 """
        if request.args.get("type") == "step":
            step_skip = [{"label": "自定义变量", "value": "variable"}, {"label": "自定义函数", "value": "func"}]
            return app.restful.success(data=skip_if_data_source_mapping + step_skip)
        return app.restful.success(data=skip_if_data_source_mapping)


class GetConfByNameView(NotLoginView):

    def get(self):
        """ 根据配置名获取配置，不需要登录 """
        name = request.args.get("name")
        return app.restful.success(data=Config.get_first(name=name).value)


class ConfigView(LoginRequiredView):

    def get(self):
        """ 获取配置 """
        form = GetConfigForm().do_validate()
        return app.restful.success("获取成功", data=form.conf.to_dict())

    def post(self):
        """ 新增配置 """
        form = PostConfigForm().do_validate()
        conf = Config().create(form.data)
        return app.restful.success("新增成功", data=conf.to_dict())

    def put(self):
        """ 修改配置 """
        form = PutConfigForm().do_validate()
        form.conf.update(form.data)
        return app.restful.success("修改成功", data=form.conf.to_dict())

    def delete(self):
        """ 删除配置 """
        form = DeleteConfigForm().do_validate()
        form.conf.delete()
        return app.restful.success("删除成功")


config_blueprint.add_url_rule("/config", view_func=ConfigView.as_view("ConfigView"))
config_blueprint.add_url_rule("/config/list", view_func=GetConfListView.as_view("GetConfListView"))
config_blueprint.add_url_rule("/config/byName", view_func=GetConfByNameView.as_view("GetConfByNameView"))
config_blueprint.add_url_rule("/config/skipIfType", view_func=GetSkipIfTypeView.as_view("GetSkipIfTypeView"))
config_blueprint.add_url_rule("/config/runModel", view_func=GetRunTestModelView.as_view("GetRunTestModelView"))
config_blueprint.add_url_rule("/config/skipIfDataSource",
                              view_func=GetSkipIfDataSourceView.as_view("GetSkipIfDataSourceView"))
