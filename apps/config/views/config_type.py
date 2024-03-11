# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import config_blueprint
from ..model_factory import ConfigType
from ..forms.config_type import GetConfigTypeForm, DeleteConfigTypeForm, PostConfigTypeForm, PutConfigTypeForm, \
    GetConfigTypeListForm


@config_blueprint.login_get("/type/list")
def config_get_config_type_list():
    form = GetConfigTypeListForm()
    if form.detail:
        get_filed = [ConfigType.id, ConfigType.name, ConfigType.desc, ConfigType.create_user]
    else:
        get_filed = ConfigType.get_simple_filed_list()
    return app.restful.get_success(ConfigType.make_pagination(form, get_filed=get_filed))


@config_blueprint.login_get("/type")
def config_get_config_type():
    """ 获取配置类型 """
    form = GetConfigTypeForm()
    return app.restful.get_success(form.conf_type.to_dict())


@config_blueprint.login_post("/type")
def config_add_config_type():
    """ 新增配置类型 """
    form = PostConfigTypeForm()
    ConfigType.model_batch_create([c_type.model_dump() for c_type in form.data_list])
    return app.restful.add_success()


@config_blueprint.login_put("/type")
def config_change_config_type():
    """ 修改配置类型 """
    form = PutConfigTypeForm()
    ConfigType.query.filter(ConfigType.id == form.id).update(form.model_dump())
    return app.restful.change_success()


@config_blueprint.login_delete("/type")
def config_delete_config_type():
    """ 删除配置类型 """
    form = DeleteConfigTypeForm()
    ConfigType.delete_by_id(form.id)
    return app.restful.delete_success()
