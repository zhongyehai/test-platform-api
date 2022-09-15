# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.api_test import api_test
from app.api_test.models.module import ApiModule as Module
from app.api_test.forms.module import AddModelForm, EditModelForm, FindModelForm, DeleteModelForm, GetModelForm
from app.baseView import LoginRequiredView

ns = api_test.namespace("module", description="模块管理相关接口")


@ns.route('/list/')
class ApiModuleListView(LoginRequiredView):

    def get(self):
        """ 模块列表 """
        form = FindModelForm()
        if form.validate():
            return app.restful.get_success(data=Module.make_pagination(form))
        return app.restful.fail(form.get_error())


@ns.route('/tree/')
class ApiModuleTreeView(LoginRequiredView):

    def get(self):
        """ 获取当前服务下的模块树 """
        project_id = int(request.args.get('project_id'))
        module_list = [
            module.to_dict() for module in Module.query.filter_by(
                project_id=project_id).order_by(Module.parent.asc()).all()
        ]
        return app.restful.success(data=module_list)


@ns.route('/')
@api_test.doc(title='模块管理', description='模块管理接口')
class ApiModuleView(LoginRequiredView):
    """ 模块管理 """

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
            form.num.data = Module.get_insert_num(project_id=form.project_id.data)
            new_model = Module().create(form.data)
            setattr(new_model, 'children', [])
            return app.restful.success(f'名为【{form.name.data}】的模块创建成功', new_model.to_dict())
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
