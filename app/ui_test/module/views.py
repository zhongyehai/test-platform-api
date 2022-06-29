# -*- coding: utf-8 -*-

from flask import request

from app.utils import restful
from app.utils.required import login_required
from app.ui_test import ui_test
from app.baseView import BaseMethodView
from .models import UiModule
from .forms import AddModelForm, EditModelForm, FindModelForm, DeleteModelForm, GetModelForm


@ui_test.route('/module/list', methods=['GET'])
@login_required
def ui_get_module_list():
    """ 模块列表 """
    form = FindModelForm()
    if form.validate():
        return restful.get_success(data=UiModule.make_pagination(form))
    return restful.fail(form.get_error())


@ui_test.route('/module/tree', methods=['GET'])
@login_required
def ui_module_tree():
    """ 获取当前服务下的模块树 """
    project_id = int(request.args.get('project_id'))
    module_list = [
        module.to_dict() for module in UiModule.query.filter_by(
            project_id=project_id).order_by(UiModule.parent.asc()).all()
    ]
    return restful.success(data=module_list)


class UiModuleView(BaseMethodView):
    """ 模块管理 """

    def get(self):
        form = GetModelForm()
        if form.validate():
            return restful.get_success(data=form.module.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        form = AddModelForm()
        if form.validate():
            form.num.data = UiModule.get_insert_num(project_id=form.project_id.data)
            new_model = UiModule().create(form.data)
            setattr(new_model, 'children', [])
            return restful.success(f'模块【{form.name.data}】创建成功', new_model.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditModelForm()
        if form.validate():
            form.old_module.update(form.data)
            return restful.success(f'模块【{form.name.data}】修改成功', form.old_module.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteModelForm()
        if form.validate():
            form.module.delete()
            return restful.success(f'模块【{form.module.name}】删除成功')
        return restful.fail(form.get_error())


ui_test.add_url_rule('/module', view_func=UiModuleView.as_view('ui_module'))
