# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.api_test.blueprint import api_test
from app.api_test.models.module import ApiModule as Module
from app.api_test.forms.module import AddModelForm, EditModelForm, FindModelForm, DeleteModelForm, GetModelForm
from app.baseView import LoginRequiredView
from app.busines import ModuleBusiness


class ApiModuleListView(LoginRequiredView):

    def get(self):
        """ 模块列表 """
        form = FindModelForm().do_validate()
        return app.restful.get_success(data=Module.make_pagination(form))


class ApiModuleTreeView(LoginRequiredView):

    def get(self):
        """ 获取当前服务下的模块树 """
        project_id = int(request.args.get('project_id'))
        module_list = [
            module.to_dict() for module in Module.query.filter_by(
                project_id=project_id).order_by(Module.parent.asc()).all()
        ]
        return app.restful.success(data=module_list)


class ApiModuleView(LoginRequiredView):
    """ 模块管理 """

    def get(self):
        """ 获取模块 """
        form = GetModelForm().do_validate()
        return app.restful.get_success(data=form.module.to_dict())

    def post(self):
        """ 新增模块 """
        form = AddModelForm().do_validate()
        new_model = ModuleBusiness.post(form, Module)
        return app.restful.success(f'名为【{form.name.data}】的模块创建成功', new_model.to_dict())

    def put(self):
        """ 修改模块 """
        form = EditModelForm().do_validate()
        form.old_module.update(form.data)
        return app.restful.success(f'模块【{form.name.data}】修改成功', form.old_module.to_dict())

    def delete(self):
        """ 删除模块 """
        form = DeleteModelForm().do_validate()
        form.module.delete()
        return app.restful.success(f'模块【{form.module.name}】删除成功')


api_test.add_url_rule('/module', view_func=ApiModuleView.as_view('ApiModuleView'))
api_test.add_url_rule('/module/list', view_func=ApiModuleListView.as_view('ApiModuleListView'))
api_test.add_url_rule('/module/tree', view_func=ApiModuleTreeView.as_view('ApiModuleTreeView'))
