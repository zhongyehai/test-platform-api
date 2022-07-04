# -*- coding: utf-8 -*-
from app.utils import restful
from app.utils.required import login_required
from app.api_test import api_test
from app.baseView import BaseMethodView
from app.api_test.models.project import ApiProject, ApiProjectEnv
from app.api_test.forms.project import (
    AddProjectForm, EditProjectForm, FindProjectForm, DeleteProjectForm, GetProjectByIdForm,
    EditEnv, AddEnv, FindEnvForm, SynchronizationEnvForm
)


@api_test.route('/project/all', methods=['GET'])
@login_required
def api_project_all():
    """ 所有服务列表 """
    return restful.success(data=[project.to_dict() for project in ApiProject.get_all()])


@api_test.route('/project/list', methods=['GET'])
@login_required
def api_project_list():
    """ 查找服务列表 """
    form = FindProjectForm()
    if form.validate():
        return restful.success(data=ApiProject.make_pagination(form))
    return restful.fail(form.get_error())


class ApiProjectView(BaseMethodView):
    """ 服务管理 """

    def get(self):
        """ 获取服务 """
        form = GetProjectByIdForm()
        if form.validate():
            return restful.success(data=form.project.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        """ 新增服务 """
        form = AddProjectForm()
        if form.validate():
            project = ApiProject().create(form.data, 'variables', 'headers', 'func_files')
            ApiProjectEnv.create_env(project.id)  # 新增服务的时候，一并把环境设置齐全
            return restful.success(f'服务【{form.name.data}】新建成功', project.to_dict())
        return restful.fail(msg=form.get_error())

    def put(self):
        """ 修改服务 """
        form = EditProjectForm()
        if form.validate():
            form.project.update(form.data, 'variables', 'headers', 'func_files')
            return restful.success(f'服务【{form.name.data}】修改成功', form.project.to_dict())
        return restful.fail(msg=form.get_error())

    def delete(self):
        """ 删除服务 """
        form = DeleteProjectForm()
        if form.validate():
            form.project.delete()
            # 删除服务的时候把环境也删掉
            for env in ApiProjectEnv.get_all(project_id=form.project.id):
                env.delete()
            return restful.success(msg=f'服务【{form.project.name}】删除成功')
        return restful.fail(form.get_error())


@api_test.route('/project/env/synchronization', methods=['POST'])
@login_required
def api_project_env_synchronization():
    """ 同步环境数据 """
    form = SynchronizationEnvForm()
    if form.validate():
        from_env = ApiProjectEnv.get_first(project_id=form.projectId.data, env=form.envFrom.data)
        synchronization_result = ApiProjectEnv.synchronization(
            from_env, form.envTo.data, ['variables', 'headers', 'func_files']
        )
        return restful.success('同步成功', data=synchronization_result)
    return restful.fail(form.get_error())


class ApiProjectEnvView(BaseMethodView):
    """ 服务环境管理 """

    def get(self):
        """ 获取服务环境 """
        form = FindEnvForm()
        if form.validate():
            return restful.success(data=form.env_data.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        """ 新增服务环境 """
        form = AddEnv()
        if form.validate():
            env = ApiProjectEnv().create(form.data, 'variables', 'headers', 'func_files')
            return restful.success(f'环境新建成功', env.to_dict())
        return restful.fail(msg=form.get_error())

    def put(self):
        """ 修改服务环境 """
        form = EditEnv()
        if form.validate():
            form.env_data.update(form.data, 'variables', 'headers', 'func_files')

            # 修改环境的时候，如果是测试环境，一并把服务的测试环境地址更新
            if form.env_data.env == 'test':
                form.project.update({'test': form.env_data.host})

            # 更新环境的时候，把环境的头部信息、变量的key一并同步到其他环境
            env_list = [
                env.env for env in ApiProjectEnv.get_all(project_id=form.project_id.data) if env.env != form.env_data.env
            ]
            ApiProjectEnv.synchronization(form.env_data, env_list, ['variables', 'headers', 'func_files'])
            return restful.success(f'环境修改成功', form.env_data.to_dict())
        return restful.fail(msg=form.get_error())


api_test.add_url_rule('/project', view_func=ApiProjectView.as_view('api_project'))
api_test.add_url_rule('/project/env', view_func=ApiProjectEnvView.as_view('api_project_env'))
