# -*- coding: utf-8 -*-
from flask import current_app as app

from ..model_factory import Config
from ..blueprint import config_blueprint
from ..forms.config import GetConfigForm, DeleteConfigForm, PostConfigForm, PutConfigForm, GetConfigListForm, \
    GetConfigValueForm, GetSkipIfConfigForm, GetFindElementByForm


@config_blueprint.login_get("/config/list")
def config_get_config_list():
    form = GetConfigListForm()
    if form.detail:
        get_filed = [Config.id, Config.name, Config.value, Config.desc, Config.type, Config.update_user]
    else:
        get_filed = [Config.id, Config.name, Config.value]
    return app.restful.get_success(Config.make_pagination(form, get_filed=get_filed))


@config_blueprint.get("/config/by/code")
def config_get_config_by_code():
    """ 根据配置名获取配置，不需要登录 """
    return app.restful.get_success(GetConfigValueForm().conf)


@config_blueprint.login_get("/config")
def config_get_config():
    """ 获取配置 """
    form = GetConfigForm()
    return app.restful.get_success(form.conf.to_dict())


@config_blueprint.login_post("/config")
def config_add_config():
    """ 新增配置 """
    form = PostConfigForm()
    Config.model_create(form.model_dump())
    return app.restful.add_success()


@config_blueprint.login_put("/config")
def config_change_config():
    """ 修改配置 """
    form = PutConfigForm()
    Config.query.filter(Config.id == form.id).update(form.model_dump())
    return app.restful.change_success()


@config_blueprint.login_delete("/config")
def config_delete_config():
    """ 删除配置 """
    form = DeleteConfigForm()
    form.conf.delete()
    return app.restful.delet_success()


@config_blueprint.get("/config/skip-if")
def config_get_config_skip_if_data_source():
    """ 获取跳过条件数据源 """
    form = GetSkipIfConfigForm()
    return app.restful.get_success(form.data)


@config_blueprint.get("/config/find-element-by")
def config_get_config_find_element_by():
    """ 获取定位方式数据源 """
    form = GetFindElementByForm()
    return app.restful.get_success(form.data)
