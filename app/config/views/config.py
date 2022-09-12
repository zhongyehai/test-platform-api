# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.baseView import LoginRequiredView, NotLoginView
from app.config.models.config import Config
from app.config.forms.config import (
    GetConfigForm, DeleteConfigForm, PostConfigForm, PutConfigForm, GetConfigListForm
)
from app.config import config
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
            config = Config().create(form.data)
            return app.restful.success('新增成功', data=config.to_dict())
        return app.restful.error(form.get_error())

    @admin_required
    def put(self):
        """ 修改配置 """
        form = PutConfigForm()
        if form.validate():
            form.conf.update(form.data)
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
