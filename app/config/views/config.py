# -*- coding: utf-8 -*-

from flask import current_app as app, request

from app.api_test.models.project import ApiProjectEnv
from app.baseView import LoginRequiredView, NotLoginView
from app.config.models.config import Config
from app.config.forms.config import (
    GetConfigForm, DeleteConfigForm, PostConfigForm, PutConfigForm, GetConfigListForm
)
from app.config import config
from app.web_ui_test.models.project import WebUiProjectEnv
from config.config import skip_if_type_mapping, skip_if_data_source_mapping
from utils.required import admin_required

ns = config.namespace("config", description="配置管理相关接口")


@ns.route('/list/')
class GetConfListView(LoginRequiredView):

    def get(self):
        form = GetConfigListForm()
        if form.validate():
            return app.restful.success(data=Config.make_pagination(form))
        return app.restful.error(form.get_error())


@ns.route('/runModel/')
class GetRunTestModelView(NotLoginView):

    def get(self):
        """ 获取执行模式 """
        return app.restful.success(data={0: "串行执行", 1: "并行执行"})


@ns.route('/skipIfType/')
class GetSkipIfTypeView(NotLoginView):

    def get(self):
        """ 获取跳过条件类型 """
        return app.restful.success(data=skip_if_type_mapping)


@ns.route('/skipIfDataSource/')
class GetSkipIfDataSourceView(NotLoginView):

    def get(self):
        """ 获取跳过条件数据源 """
        if request.args.get('type') == 'step':
            step_skip = [{"label": "自定义变量", "value": "variable"}, {"label": "自定义函数", "value": "func"}]
            return app.restful.success(data=skip_if_data_source_mapping + step_skip)
        return app.restful.success(data=skip_if_data_source_mapping)


@ns.route('/byName/')
class GetConfByNameView(NotLoginView):

    def get(self):
        """ 根据配置名获取配置，不需要登录 """
        return app.restful.success(data=Config.get_first(name=request.args.get('name')).to_dict())


@ns.route('/')
class ConfigView(LoginRequiredView):

    def get(self):
        """ 获取配置 """
        form = GetConfigForm()
        if form.validate():
            return app.restful.success('获取成功', data=form.conf.to_dict())
        return app.restful.error(form.get_error())

    def post(self):
        """ 新增配置 """
        form = PostConfigForm()
        if form.validate():
            conf = Config().create(form.data)
            return app.restful.success('新增成功', data=conf.to_dict())
        return app.restful.error(form.get_error())

    @admin_required
    def put(self):
        """ 修改配置 """
        form = PutConfigForm()
        if form.validate():
            form.conf.update(form.data)

            # 同步环境信息
            new_env_list = Config.get_new_env_list(form)
            if new_env_list:
                ApiProjectEnv.create_env(env_list=new_env_list)
                WebUiProjectEnv.create_env(env_list=new_env_list)

            return app.restful.success('修改成功', data=form.conf.to_dict())
        return app.restful.error(form.get_error())

    @admin_required
    def delete(self):
        """ 删除配置 """
        form = DeleteConfigForm()
        if form.validate():
            form.conf.delete()
            return app.restful.success('删除成功')
        return app.restful.error(form.get_error())
