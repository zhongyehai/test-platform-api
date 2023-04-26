# -*- coding: utf-8 -*-
from flask import current_app as app

from app.baseView import LoginRequiredView, AdminRequiredView
from app.config.models.config import ConfigType, db
from app.config.forms.config import (
    GetConfigTypeForm, DeleteConfigTypeForm, PostConfigTypeForm, PutConfigTypeForm, GetConfigTypeListForm
)
from app.config.blueprint import config_blueprint


class GetConfTypeListView(LoginRequiredView):

    def get(self):
        form = GetConfigTypeListForm().do_validate()
        return app.restful.success(data=ConfigType.make_pagination(form))


class ConfigTypeView(LoginRequiredView):

    def get(self):
        """ 获取配置类型 """
        form = GetConfigTypeForm().do_validate()
        return app.restful.success("获取成功", data=form.conf.to_dict())

    def post(self):
        """ 新增配置类型 """
        form = PostConfigTypeForm().do_validate()
        config_type = ConfigType().create(form.data)
        return app.restful.success("新增成功", data=config_type.to_dict())

    def put(self):
        """ 修改配置类型 """
        form = PutConfigTypeForm().do_validate()
        form.conf_type.update(form.data)
        return app.restful.success("修改成功", data=form.conf_type.to_dict())

    def delete(self):
        """ 删除配置类型 """
        form = DeleteConfigTypeForm().do_validate()
        form.config_type.delete()
        return app.restful.success("删除成功")


config_blueprint.add_url_rule("/type", view_func=ConfigTypeView.as_view("ConfigTypeView"))
config_blueprint.add_url_rule("/type/list", view_func=GetConfTypeListView.as_view("GetConfTypeListView"))
