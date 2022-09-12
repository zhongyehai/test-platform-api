# -*- coding: utf-8 -*-

from flask import request, current_app as app

from app.baseView import LoginRequiredView
from app.web_ui_test import web_ui_test
from app.web_ui_test.models.module import UiModule
from app.web_ui_test.forms.module import AddModelForm, EditModelForm, FindModelForm, DeleteModelForm, GetModelForm

ns = web_ui_test.namespace("module", description="模块管理相关接口")


@ns.route('/list/')
class WebUiGetModuleListView(LoginRequiredView):

    def get(self):
        """ 获取模块列表 """
        form = FindModelForm()
        if form.validate():
            return app.restful.get_success(data=UiModule.make_pagination(form))
        return app.restful.fail(form.get_error())


@ns.route('/tree/')
class WebUiGetModuleTreeView(LoginRequiredView):

    def get(self):
        """ 获取指定服务下的模块树 """
        project_id = int(request.args.get('project_id'))
        module_list = [
            module.to_dict() for module in UiModule.query.filter_by(
                project_id=project_id).order_by(UiModule.parent.asc()).all()
        ]
        return app.restful.success(data=module_list)


@ns.route('/')
class WebUiModuleView(LoginRequiredView):

    def get(self):
        """ 获取模块 """
        form = GetModelForm()
        if form.validate():
            return app.restful.get_success(data=form.module.to_dict())
        return app.restful.fail(form.get_error())

    def post(self):
        """ 新增模块 """
        form = AddModelForm()
        if form.validate():
            form.num.data = UiModule.get_insert_num(project_id=form.project_id.data)
            new_model = UiModule().create(form.data)
            setattr(new_model, 'children', [])
            return app.restful.success(f'模块【{form.name.data}】创建成功', new_model.to_dict())
        return app.restful.fail(form.get_error())

    def put(self):
        """ 修改模块 """
        form = EditModelForm()
        if form.validate():
            form.old_module.update(form.data)
            return app.restful.success(f'模块【{form.name.data}】修改成功', form.old_module.to_dict())
        return app.restful.fail(form.get_error())

    def delete(self):
        """ 删除模块 """
        form = DeleteModelForm()
        if form.validate():
            form.module.delete()
            return app.restful.success(f'模块【{form.module.name}】删除成功')
        return app.restful.fail(form.get_error())
