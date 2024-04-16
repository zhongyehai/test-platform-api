# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import api_test
from ..model_factory import ApiModule as Module
from ..forms.module import (
    AddModuleForm, EditModuleForm, DeleteModuleForm, GetModuleForm, GetModuleTreeForm, GetModuleListForm
)


@api_test.login_get("/module/list")
def api_get_module_list():
    """ 模块列表 """
    form = GetModuleListForm()
    get_filed = [Module.id, Module.name, Module.parent, Module.project_id, Module.controller]
    return app.restful.get_success(Module.make_pagination(form, get_filed=get_filed))


@api_test.login_get("/module/tree")
def api_get_module_tree():
    """ 获取当前服务下的模块树 """
    form = GetModuleTreeForm()
    module_list = [
        module.to_dict() for module in Module.query.filter_by(
            project_id=form.project_id).order_by(Module.parent.asc()).all()
    ]
    return app.restful.get_success(module_list)


@api_test.login_get("/module")
def api_get_module():
    """ 获取模块 """
    form = GetModuleForm()
    return app.restful.get_success(form.module.to_dict())


@api_test.login_post("/module")
def api_add_module():
    """ 新增模块 """
    form = AddModuleForm()
    if len(form.data_list) == 1:
        return app.restful.add_success(Module.model_create_and_get(form.data_list[0]).to_dict())
    Module.model_batch_create(form.data_list)
    return app.restful.add_success()


@api_test.login_put("/module")
def api_change_module():
    """ 修改模块 """
    form = EditModuleForm()
    form.module.model_update(form.model_dump())
    return app.restful.change_success(form.module.to_dict())


@api_test.login_delete("/module")
def api_delete_module():
    """ 删除模块 """
    form = DeleteModuleForm()
    Module.delete_by_id(form.id)
    return app.restful.delete_success()
