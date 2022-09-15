# -*- coding: utf-8 -*-
from flask import current_app as app

from app.api_test import api_test
from app.api_test.models.project import ApiProject as Project, ApiProjectEnv as ProjectEnv
from app.api_test.forms.project import (
    AddProjectForm, EditProjectForm, FindProjectForm, DeleteProjectForm, GetProjectByIdForm,
    EditEnv, AddEnv, FindEnvForm, SynchronizationEnvForm
)
from app.baseView import LoginRequiredView

ns = api_test.namespace("project", description="服务管理相关接口")


@ns.route('/all/')
class ApiProjectAllView(LoginRequiredView):

    def get(self):
        """ 所有服务列表 """
        return app.restful.success(data=[project.to_dict() for project in Project.get_all()])


@ns.route('/list/')
class ApiProjectListView(LoginRequiredView):

    def get(self):
        """ 获取服务列表 """
        form = FindProjectForm()
        if form.validate():
            return app.restful.success(data=Project.make_pagination(form))
        return app.restful.fail(form.get_error())


@ns.route('/')
@api_test.doc(title='服务管理', description='服务管理接口')
class ApiProjectView(LoginRequiredView):
    """ 服务管理 """

    def get(self):
        """ 获取服务 """
        form = GetProjectByIdForm()
        if form.validate():
            return app.restful.success(data=form.project.to_dict())
        return app.restful.fail(form.get_error())

    def post(self):
        """ 新增服务 """
        form = AddProjectForm()
        if form.validate():
            project = Project().create(form.data)
            ProjectEnv.create_env(project.id)  # 新增服务的时候，一并把环境设置齐全
            return app.restful.success(f'服务【{form.name.data}】新建成功', project.to_dict())
        return app.restful.fail(msg=form.get_error())

    def put(self):
        """ 修改服务 """
        form = EditProjectForm()
        if form.validate():
            form.project.update(form.data)
            return app.restful.success(f'服务【{form.name.data}】修改成功', form.project.to_dict())
        return app.restful.fail(msg=form.get_error())

    def delete(self):
        """ 删除服务 """
        form = DeleteProjectForm()
        if form.validate():
            form.project.delete_current_and_env()
            return app.restful.success(msg=f'服务【{form.project.name}】删除成功')
        return app.restful.fail(form.get_error())


@ns.route('/env/synchronization/')
class ApiProjectEnvViewSynchronizationView(LoginRequiredView):

    def post(self):
        """ 同步环境数据 """
        form = SynchronizationEnvForm()
        if form.validate():
            from_env = ProjectEnv.get_first(project_id=form.projectId.data, env=form.envFrom.data)
            synchronization_result = ProjectEnv.synchronization(from_env, form.envTo.data, ['variables', 'headers'])
            return app.restful.success('同步成功', data=synchronization_result)
        return app.restful.fail(form.get_error())


@ns.route('/env/')
@api_test.doc(title='服务环境管理', description='服务环境管理接口')
class ApiProjectEnvView(LoginRequiredView):
    """ 服务环境管理 """

    def get(self):
        """ 获取服务环境 """
        form = FindEnvForm()
        if form.validate():
            return app.restful.success(data=form.env_data.to_dict())
        return app.restful.fail(form.get_error())

    def post(self):
        """ 新增服务环境 """
        form = AddEnv()
        if form.validate():
            env = ProjectEnv().create(form.data)
            return app.restful.success(f'环境新建成功', env.to_dict())
        return app.restful.fail(msg=form.get_error())

    def put(self):
        """ 修改服务环境 """
        form = EditEnv()
        if form.validate():
            form.env_data.update(form.data)

            # 修改环境的时候，如果是测试环境，一并把服务的测试环境地址更新
            if form.env_data.env == 'test':
                form.project.update({'test': form.env_data.host})

            # 更新环境的时候，把环境的头部信息、变量的key一并同步到其他环境
            env_list = [
                env.env for env in ProjectEnv.get_all(project_id=form.project_id.data) if
                env.env != form.env_data.env
            ]
            ProjectEnv.synchronization(form.env_data, env_list, ['variables', 'headers'])
            return app.restful.success(f'环境修改成功', form.env_data.to_dict())
        return app.restful.fail(msg=form.get_error())
