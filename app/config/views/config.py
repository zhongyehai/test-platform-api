# -*- coding: utf-8 -*-
from flask import current_app as app, request, views

from app.config.models.config import Config, ConfigType, db
from app.config.forms.config import (
    GetConfigTypeForm, DeleteConfigTypeForm, PostConfigTypeForm, PutConfigTypeForm, GetConfigTypeListForm,
    GetConfigForm, DeleteConfigForm, PostConfigForm, PutConfigForm, GetConfigListForm
)
from app.config import config


@config.route('/type/list', methods=['GET'])
def conf_type_list():
    form = GetConfigTypeListForm()
    if form.validate():
        return app.restful.success(data=ConfigType.make_pagination(form))
    return app.restful.error(form.get_error())


class ConfigTypeView(views.MethodView):

    def get(self):
        form = GetConfigTypeForm()
        if form.validate():
            return app.restful.success('获取成功', data=form.conf.to_dict())
        return app.restful.error(form.get_error())

    def post(self):
        form = PostConfigTypeForm()
        if form.validate():
            with db.auto_commit():
                config_type = ConfigType()
                config_type.create(form.data)
                db.session.add(config_type)
            return app.restful.success('新增成功', data=config_type.to_dict())
        return app.restful.error(form.get_error())

    def put(self):
        form = PutConfigTypeForm()
        if form.validate():
            with db.auto_commit():
                form.conf_type.update(form.data)
            return app.restful.success('修改成功', data=form.conf_type.to_dict())
        return app.restful.error(form.get_error())

    def delete(self):
        form = DeleteConfigTypeForm()
        if form.validate():
            with db.auto_commit():
                db.session.delete(form.config_type)
            return app.restful.success('删除成功')
        return app.restful.error(form.get_error())


@config.route('/list', methods=['GET'])
def conf_list():
    form = GetConfigListForm()
    if form.validate():
        return app.restful.success(data=Config.make_pagination(form))
    return app.restful.error(form.get_error())


@config.route('/runModel', methods=['GET'])
def get_run_model():
    """ 获取执行模式 """
    return app.restful.success(data={0: "串行执行", 1: "并行执行"})


@config.route('/configByName', methods=['GET'])
def get_conf_by_name_not_login_required():
    """ 根据配置名获取配置 """
    return app.restful.success(data=Config.get_first(name=request.args.get('name')).to_dict())


class ConfigView(views.MethodView):

    def get(self):
        form = GetConfigForm()
        if form.validate():
            return app.restful.success('获取成功', data=form.conf.to_dict())
        return app.restful.error(form.get_error())

    def post(self):
        form = PostConfigForm()
        if form.validate():
            config = Config().create(form.data)
            return app.restful.success('新增成功', data=config.to_dict())
        return app.restful.error(form.get_error())

    def put(self):
        form = PutConfigForm()
        if form.validate():
            form.conf.update(form.data)
            return app.restful.success('修改成功', data=form.conf.to_dict())
        return app.restful.error(form.get_error())

    def delete(self):
        form = DeleteConfigForm()
        if form.validate():
            form.conf.delete()
            return app.restful.success('删除成功')
        return app.restful.error(form.get_error())


config.add_url_rule('/', view_func=ConfigView.as_view('config'))
config.add_url_rule('/type', view_func=ConfigTypeView.as_view('configType'))
