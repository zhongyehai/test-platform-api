# -*- coding: utf-8 -*-
from flask import request, current_app as app

from app.busines import ModuleBusiness
from app.app_ui_test.blueprint import app_test
from app.app_ui_test.models.module import AppUiModule as Module
from app.app_ui_test.forms.module import AddModelForm, EditModelForm, FindModelForm, DeleteModelForm, GetModelForm


@app_test.login_get("/module/list")
def app_get_module_list():
    """ 获取模块列表 """
    form = FindModelForm().do_validate()
    return app.restful.get_success(data=Module.make_pagination(form))


@app_test.login_get("/module/tree")
def app_get_module_tree():
    """ 获取指定服务下的模块树 """
    project_id = int(request.args.get("project_id"))
    module_list = [
        module.to_dict() for module in Module.query.filter_by(
            project_id=project_id).order_by(Module.parent.asc()).all()
    ]
    return app.restful.success(data=module_list)


@app_test.login_get("/module")
def app_get_module():
    """ 获取模块 """
    form = GetModelForm().do_validate()
    return app.restful.get_success(data=form.module.to_dict())


@app_test.login_post("/module")
def app_add_module():
    """ 新增模块 """
    form = AddModelForm().do_validate()
    new_model = ModuleBusiness.post(form, Module)
    return app.restful.success(f"模块【{form.name.data}】创建成功", new_model.to_dict())


@app_test.login_put("/module")
def app_change_module():
    """ 修改模块 """
    form = EditModelForm().do_validate()
    form.old_module.update(form.data)
    return app.restful.success(f"模块【{form.name.data}】修改成功", form.old_module.to_dict())


@app_test.login_delete("/module")
def app_delete_module():
    """ 删除模块 """
    form = DeleteModelForm().do_validate()
    form.module.delete()
    return app.restful.success(f"模块【{form.module.name}】删除成功")
