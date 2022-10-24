# -*- coding: utf-8 -*-
from flask import current_app as app

from app.baseView import LoginRequiredView
from app.web_ui_test import web_ui_test
from app.web_ui_test.models.project import WebUiProject as Project, WebUiProjectEnv as ProjectEnv
from app.web_ui_test.forms.project import (
    AddUiProjectForm, EditUiProjectForm, FindUiProjectForm, DeleteUiProjectForm, GetUiProjectByIdForm,
    EditEnv, AddEnv, FindEnvForm, SynchronizationEnvForm
)

ns = web_ui_test.namespace("project", description="项目管理相关接口")


@ns.route('/all/')
class WebUiProjectAllView(LoginRequiredView):

    def get(self):
        """ 获取所有项目列表 """
        return app.restful.success(data=[project.to_dict() for project in Project.get_all()])


@ns.route('/list/')
class WebUiProjectListView(LoginRequiredView):

    def get(self):
        """ 查找项目列表 """
        form = FindUiProjectForm()
        if form.validate():
            return app.restful.success(data=Project.make_pagination(form))
        return app.restful.fail(form.get_error())


@ns.route('/')
class WebProjectView(LoginRequiredView):

    def get(self):
        """ 获取项目 """
        form = GetUiProjectByIdForm()
        if form.validate():
            return app.restful.success(data=form.project.to_dict())
        return app.restful.fail(form.get_error())

    def post(self):
        """ 新增项目 """
        form = AddUiProjectForm()
        if form.validate():
            form.num.data = Project.get_insert_num()
            project = Project().create(form.data)
            ProjectEnv.create_env(project.id)  # 新增项目的时候，一并把环境设置齐全
            return app.restful.success(f'项目【{form.name.data}】新建成功', project.to_dict())
        return app.restful.fail(msg=form.get_error())

    def put(self):
        """ 修改项目 """
        form = EditUiProjectForm()
        if form.validate():
            form.project.update(form.data)
            return app.restful.success(f'项目【{form.name.data}】修改成功', form.project.to_dict())
        return app.restful.fail(msg=form.get_error())

    def delete(self):
        """ 删除项目 """
        form = DeleteUiProjectForm()
        if form.validate():
            form.project.delete_current_and_env()
            return app.restful.success(msg=f'项目【{form.project.name}】删除成功')
        return app.restful.fail(form.get_error())


@ns.route('/env/synchronization/')
class WebUiProjectEnvSynchronizationView(LoginRequiredView):

    def post(self):
        """ 同步环境数据 """
        form = SynchronizationEnvForm()
        if form.validate():
            from_env = ProjectEnv.get_first(project_id=form.projectId.data, env=form.envFrom.data)
            synchronization_result = ProjectEnv.synchronization(
                from_env,
                form.envTo.data,
                ["variables"]
            )
            return app.restful.success('同步成功', data=synchronization_result)
        return app.restful.fail(form.get_error())


@ns.route('/env/')
class WebUiProjectEnvView(LoginRequiredView):

    def get(self):
        """ 获取项目环境 """
        form = FindEnvForm()
        if form.validate():
            return app.restful.success(data=form.env_data.to_dict())
        return app.restful.fail(form.get_error())

    def post(self):
        """ 新增项目环境 """
        form = AddEnv()
        if form.validate():
            env = ProjectEnv().create(form.data)
            return app.restful.success(f'环境新建成功', env.to_dict())
        return app.restful.fail(msg=form.get_error())

    def put(self):
        """ 修改项目环境 """
        form = EditEnv()
        if form.validate():
            form.env_data.update(form.data)

            # 更新环境的时候，把环境的头部信息、变量的key一并同步到其他环境
            env_list = [
                env.env for env in ProjectEnv.get_all(project_id=form.project_id.data) if env.env != form.env_data.env
            ]
            ProjectEnv.synchronization(
                form.env_data,
                env_list,
                ["variables"]
            )
            return app.restful.success(f'环境保存成功', form.env_data.to_dict())
        return app.restful.fail(msg=form.get_error())
