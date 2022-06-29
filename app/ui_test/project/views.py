# -*- coding: utf-8 -*-

from app.utils import restful
from app.utils.parse import parse_list_to_dict, parse_dict_to_list
from app.utils.required import login_required
from app.ui_test import ui_test
from app.baseView import BaseMethodView
from .models import UiProject, UiProjectEnv
from .forms import (
    AddUiProjectForm, EditUiProjectForm, FindUiProjectForm, DeleteUiProjectForm, GetUiProjectByIdForm,
    EditEnv, AddEnv, FindEnvForm, SynchronizationEnvForm
)


@ui_test.route('/project/all', methods=['GET'])
@login_required
def ui_project_all():
    """ 所有项目列表 """
    return restful.success(data=[project.to_dict() for project in UiProject.get_all()])


@ui_test.route('/project/list', methods=['GET'])
@login_required
def ui_project_list():
    """ 查找项目列表 """
    form = FindUiProjectForm()
    if form.validate():
        return restful.success(data=UiProject.make_pagination(form))
    return restful.fail(form.get_error())


class ProjectView(BaseMethodView):
    """ 项目管理 """

    def get(self):
        """ 获取项目 """
        form = GetUiProjectByIdForm()
        if form.validate():
            return restful.success(data=form.project.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        """ 新增项目 """
        form = AddUiProjectForm()
        if form.validate():
            project = UiProject().create(form.data, 'variables', 'headers', 'func_files')
            UiProjectEnv.create_env(project.id)  # 新增项目的时候，一并把环境设置齐全
            return restful.success(f'项目【{form.name.data}】新建成功', project.to_dict())
        return restful.fail(msg=form.get_error())

    def put(self):
        """ 修改项目 """
        form = EditUiProjectForm()
        if form.validate():
            form.project.update(form.data, 'variables', 'headers', 'func_files')
            return restful.success(f'项目【{form.name.data}】修改成功', form.project.to_dict())
        return restful.fail(msg=form.get_error())

    def delete(self):
        """ 删除项目 """
        form = DeleteUiProjectForm()
        if form.validate():
            form.project.delete()
            # 删除项目的时候把环境也删掉
            for env in UiProjectEnv.get_all(project_id=form.project.id):
                env.delete()
            return restful.success(msg=f'项目【{form.project.name}】删除成功')
        return restful.fail(form.get_error())


@ui_test.route('/project/env/synchronization', methods=['POST'])
@login_required
def project_env_synchronization():
    """ 同步环境数据 """
    form = SynchronizationEnvForm()
    if form.validate():
        from_env = UiProjectEnv.get_first(project_id=form.projectId.data, env=form.envFrom.data)
        synchronization_result = UiProjectEnv.synchronization(from_env, form.envTo.data)
        return restful.success('同步成功', data=synchronization_result)
    return restful.fail(form.get_error())


class ProjectEnvView(BaseMethodView):
    """ 项目环境管理 """

    def get(self):
        """ 获取项目环境 """
        form = FindEnvForm()
        if form.validate():
            return restful.success(data=form.env_data.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        """ 新增项目环境 """
        form = AddEnv()
        if form.validate():
            env = UiProjectEnv().create(form.data, 'variables', 'headers', 'func_files')
            return restful.success(f'环境新建成功', env.to_dict())
        return restful.fail(msg=form.get_error())

    def put(self):
        """ 修改项目环境 """
        form = EditEnv()
        if form.validate():
            form.env_data.update(form.data, 'variables', 'headers', 'func_files')

            # 修改环境的时候，如果是测试环境，一并把服务的测试环境地址更新
            if form.env_data.env == 'test':
                form.project.update({'test': form.env_data.host})

            # 更新环境的时候，把环境的头部信息、变量的key一并同步到其他环境
            env_list = [
                env.env for env in UiProjectEnv.get_all(project_id=form.project_id.data) if env.env != form.env_data.env
            ]
            UiProjectEnv.synchronization(form.env_data, env_list)

            return restful.success(f'环境保存成功', form.env_data.to_dict())
        return restful.fail(msg=form.get_error())


ui_test.add_url_rule('/project', view_func=ProjectView.as_view('ui_project'))
ui_test.add_url_rule('/project/env', view_func=ProjectEnvView.as_view('ui_project_env'))
