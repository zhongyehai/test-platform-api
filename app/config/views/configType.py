# -*- coding: utf-8 -*-
from flask import current_app as app

from app.baseView import LoginRequiredView, AdminRequiredView
from app.config.models.config import ConfigType, db
from app.config.forms.config import (
    GetConfigTypeForm, DeleteConfigTypeForm, PostConfigTypeForm, PutConfigTypeForm, GetConfigTypeListForm
)
from app.config import config

ns = config.namespace("type", description="配置类型管理相关接口")


@ns.route('/list/')
class GetConfTypeListView(LoginRequiredView):

    def get(self):
        form = GetConfigTypeListForm()
        if form.validate():
            return app.restful.success(data=ConfigType.make_pagination(form))
        return app.restful.error(form.get_error())


@ns.route('/')
class ConfigTypeView(AdminRequiredView):

    def get(self):
        """ 获取配置类型 """
        form = GetConfigTypeForm()
        if form.validate():
            return app.restful.success('获取成功', data=form.conf.to_dict())
        return app.restful.error(form.get_error())

    def post(self):
        """ 新增配置类型 """
        form = PostConfigTypeForm()
        if form.validate():
            with db.auto_commit():
                config_type = ConfigType()
                config_type.create(form.data)
                db.session.add(config_type)
            return app.restful.success('新增成功', data=config_type.to_dict())
        return app.restful.error(form.get_error())

    def put(self):
        """ 修改配置类型 """
        form = PutConfigTypeForm()
        if form.validate():
            with db.auto_commit():
                form.conf_type.update(form.data)
            return app.restful.success('修改成功', data=form.conf_type.to_dict())
        return app.restful.error(form.get_error())

    def delete(self):
        """ 删除配置类型 """
        form = DeleteConfigTypeForm()
        if form.validate():
            with db.auto_commit():
                db.session.delete(form.config_type)
            return app.restful.success('删除成功')
        return app.restful.error(form.get_error())
