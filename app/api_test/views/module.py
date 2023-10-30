# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.api_test.blueprint import api_test
from app.api_test.models.module import ApiModule as Module
from app.api_test.forms.module import AddModelForm, EditModelForm, FindModelForm, DeleteModelForm, GetModelForm
from app.busines import ModuleBusiness


@api_test.login_get("/module/list")
def api_get_module_list():
    """ 模块列表 """
    form = FindModelForm().do_validate()
    return app.restful.get_success(data=Module.make_pagination(form))


@api_test.login_get("/module/tree")
def api_get_module_tree():
    """ 获取当前服务下的模块树 """
    project_id = int(request.args.get("project_id"))
    module_list = [
        module.to_dict() for module in Module.query.filter_by(
            project_id=project_id).order_by(Module.parent.asc()).all()
    ]
    return app.restful.success(data=module_list)


@api_test.login_get("/module")
def api_get_module():
    """ 获取模块 """
    form = GetModelForm().do_validate()
    return app.restful.get_success(data=form.module.to_dict())


@api_test.login_post("/module")
def api_add_module():
    """ 新增模块 """
    form = AddModelForm().do_validate()
    new_model = ModuleBusiness.post(form, Module)
    return app.restful.success(f"名为【{form.name.data}】的模块创建成功", new_model.to_dict())


@api_test.login_put("/module")
def api_change_module():
    """ 修改模块 """
    form = EditModelForm().do_validate()
    form.old_module.update(form.data)
    return app.restful.success(f"模块【{form.name.data}】修改成功", form.old_module.to_dict())


@api_test.login_delete("/module")
def api_delete_module():
    """ 删除模块 """
    form = DeleteModelForm().do_validate()
    form.module.delete()
    return app.restful.success(f"模块【{form.module.name}】删除成功")
