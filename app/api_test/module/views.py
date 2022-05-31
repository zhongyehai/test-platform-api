# -*- coding: utf-8 -*-
from flask import request

from app.utils import restful
from app.utils.required import login_required
from app.api_test import api_test
from app.baseView import BaseMethodView
from .models import ApiModule
from .forms import AddModelForm, EditModelForm, FindModelForm, DeleteModelForm, GetModelForm


@api_test.route('/module/list', methods=['GET'])
@login_required
def api_get_module_list():
    """ 模块列表 """
    form = FindModelForm()
    if form.validate():
        return restful.get_success(data=ApiModule.make_pagination(form))
    return restful.fail(form.get_error())


@api_test.route('/module/tree', methods=['GET'])
@login_required
def api_module_tree():
    """ 获取当前服务下的模块树 """
    project_id = int(request.args.get('project_id'))
    module_list = [
        module.to_dict() for module in ApiModule.query.filter_by(
            project_id=project_id).order_by(ApiModule.parent.asc()).all()
    ]
    return restful.success(data=module_list)


class ApiModuleView(BaseMethodView):
    """ 模块管理 """

    def get(self):
        form = GetModelForm()
        if form.validate():
            return restful.get_success(data=form.module.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        form = AddModelForm()
        if form.validate():
            form.num.data = ApiModule.get_insert_num(project_id=form.project_id.data)
            new_model = ApiModule().create(form.data)
            setattr(new_model, 'children', [])
            return restful.success(f'名为【{form.name.data}】的模块创建成功', new_model.to_dict())
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
            return restful.success(f'名为【{form.module.name}】的模块删除成功')
        return restful.fail(form.get_error())


api_test.add_url_rule('/module', view_func=ApiModuleView.as_view('api_module'))
