# -*- coding: utf-8 -*-
from flask import current_app as app

from app.config.models.config import ConfigType, db
from app.config.forms.config import (
    GetConfigTypeForm, DeleteConfigTypeForm, PostConfigTypeForm, PutConfigTypeForm, GetConfigTypeListForm
)
from app.config.blueprint import config_blueprint


@config_blueprint.login_get("/type/list")
def config_get_config_type_list():
    form = GetConfigTypeListForm().do_validate()
    return app.restful.success(data=ConfigType.make_pagination(form))


@config_blueprint.login_get("/type")
def config_get_config_type():
    """ 获取配置类型 """
    form = GetConfigTypeForm().do_validate()
    return app.restful.success("获取成功", data=form.conf_type.to_dict())


@config_blueprint.login_post("/type")
def config_add_config_type():
    """ 新增配置类型 """
    form = PostConfigTypeForm().do_validate()
    config_type = ConfigType().create(form.data)
    return app.restful.success("新增成功", data=config_type.to_dict())


@config_blueprint.login_put("/type")
def config_change_config_type():
    """ 修改配置类型 """
    form = PutConfigTypeForm().do_validate()
    form.conf_type.update(form.data)
    return app.restful.success("修改成功", data=form.conf_type.to_dict())


@config_blueprint.login_delete("/type")
def config_delete_config_type():
    """ 删除配置类型 """
    form = DeleteConfigTypeForm().do_validate()
    form.config_type.delete()
    return app.restful.success("删除成功")
