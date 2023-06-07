# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.baseView import LoginRequiredView, NotLoginView
from app.config.models.config import Config
from app.config.forms.config import (
    GetConfigForm, DeleteConfigForm, PostConfigForm, PutConfigForm, GetConfigListForm
)
from app.config.blueprint import config_blueprint
from config import skip_if_type_mapping


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


class GetExtractsMappingView(NotLoginView):

    def get(self):
        """ 获取提数数据源枚举 """
        data = [
            {"label": "响应体", "value": "content"},
            {"label": "响应头部信息", "value": "headers"},
            {"label": "响应cookies", "value": "cookies"},
            {"label": "正则表达式（从响应体提取）", "value": "regexp"},
            {"label": "常量", "value": "const"},
            {"label": "自定义变量", "value": "variable"},
            {"label": "自定义函数", "value": "func"},
            {"label": "其他（常量、自定义变量、自定义函数）", "value": "other"}
        ]
        return app.restful.success(data=data)


class GetSkipIfDataSourceView(NotLoginView):

    def get(self):
        """ 获取跳过条件数据源 """
        data = [{"label": "运行环境", "value": "run_env"}]
        if request.args.get("test_type") == "appUi":
            data += [{"label": "运行服务器", "value": "run_server"}, {"label": "运行设备", "value": "run_device"}]
        if request.args.get("type") == "step":
            step_skip = [{"label": "自定义变量", "value": "variable"}, {"label": "自定义函数", "value": "func"}]
            return app.restful.success(data=data + step_skip)
        return app.restful.success(data=data)


class GetFindElementByView(NotLoginView):

    def get(self):
        """ 获取定位方式数据源 """
        data = [
            {"label": "根据id属性定位", "value": "id"},
            {"label": "根据xpath表达式定位", "value": "xpath"},
            {"label": "根据class选择器定位", "value": "class name"},
            {"label": "根据css选择器定位", "value": "css selector"},
            {"label": "根据name属性定位", "value": "name"},
            {"label": "根据tag名字定位 ", "value": "tag name"},
            {"label": "根据超链接文本定位", "value": "link text"},
            {"label": "页面地址", "value": "url"}
        ]
        if request.args.get("test_type") == "appUi":
            data += [
                {"label": "坐标定位", "value": "coordinate"},
                {"label": "accessibility_id", "value": "accessibility id"}
            ]
        return app.restful.success(data=data)


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
config_blueprint.add_url_rule("/config/extractsMapping",
                              view_func=GetExtractsMappingView.as_view("GetExtractsMappingView"))
config_blueprint.add_url_rule("/config/findElementBy",
                              view_func=GetFindElementByView.as_view("GetFindElementByView"))
