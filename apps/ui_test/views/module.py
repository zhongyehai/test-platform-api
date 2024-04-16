# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import ui_test
from ..model_factory import WebUiModule as Module
from ..forms.module import (
    AddModuleForm, EditModuleForm, DeleteModuleForm, GetModuleForm, GetModuleTreeForm, GetModuleListForm
)


@ui_test.login_get("/module/list")
def ui_get_module_list():
    """ 获取模块列表 """
    form = GetModuleListForm()
    get_filed = [Module.id, Module.name, Module.parent, Module.project_id]
    return app.restful.get_success(Module.make_pagination(form, get_filed=get_filed))


@ui_test.login_get("/module/tree")
def ui_get_module_tree():
    """ 获取指定项目下的模块树 """
    form = GetModuleTreeForm()
    module_list = [
        module.to_dict() for module in Module.query.filter_by(
            project_id=form.project_id).order_by(Module.parent.asc()).all()
    ]
    return app.restful.get_success(module_list)


@ui_test.login_get("/module")
def ui_get_module():
    """ 获取模块 """
    form = GetModuleForm()
    return app.restful.get_success(form.module.to_dict())


@ui_test.login_post("/module")
def ui_add_module():
    """ 新增模块 """
    form = AddModuleForm()
    if len(form.data_list) == 1:
        return app.restful.add_success(Module.model_create_and_get(form.data_list[0]).to_dict())
    Module.model_batch_create(form.data_list)
    return app.restful.add_success()


@ui_test.login_put("/module")
def ui_change_module():
    """ 修改模块 """
    form = EditModuleForm()
    form.module.model_update(form.model_dump())
    return app.restful.change_success(form.module.to_dict())


@ui_test.login_delete("/module")
def ui_delete_module():
    """ 删除模块 """
    form = DeleteModuleForm()
    Module.delete_by_id(form.id)
    return app.restful.delete_success()
