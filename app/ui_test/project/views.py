#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm
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
    """ 所有服务列表 """
    return restful.success(data=[project.to_dict() for project in UiProject.get_all()])


@ui_test.route('/project/list', methods=['GET'])
@login_required
def ui_project_list():
    """ 查找服务列表 """
    form = FindUiProjectForm()
    if form.validate():
        return restful.success(data=UiProject.make_pagination(form))
    return restful.fail(form.get_error())


class ProjectView(BaseMethodView):
    """ 服务管理 """

    def get(self):
        """ 获取服务 """
        form = GetUiProjectByIdForm()
        if form.validate():
            return restful.success(data=form.project.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        """ 新增服务 """
        form = AddUiProjectForm()
        if form.validate():
            project = UiProject().create(form.data, 'variables', 'headers', 'func_files')
            project.create_env()  # 新增服务的时候，一并把环境设置齐全
            return restful.success(f'服务【{form.name.data}】新建成功', project.to_dict())
        return restful.fail(msg=form.get_error())

    def put(self):
        """ 修改服务 """
        form = EditUiProjectForm()
        if form.validate():
            form.project.update(form.data, 'variables', 'headers', 'func_files')
            return restful.success(f'服务【{form.name.data}】修改成功', form.project.to_dict())
        return restful.fail(msg=form.get_error())

    def delete(self):
        """ 删除服务 """
        form = DeleteUiProjectForm()
        if form.validate():
            form.project.delete()
            # 删除服务的时候把环境也删掉
            for env in UiProjectEnv.get_all(project_id=form.project.id):
                env.delete()
            return restful.success(msg=f'服务【{form.project.name}】删除成功')
        return restful.fail(form.get_error())


@ui_test.route('/project/env/synchronization', methods=['POST'])
@login_required
def project_env_synchronization():
    """ 同步环境数据 """
    form = SynchronizationEnvForm()
    if form.validate():
        from_env = UiProjectEnv.get_first(project_id=form.projectId.data, env=form.envFrom.data)
        from_env_variable = parse_list_to_dict(form.loads(from_env.variables))
        from_env_headers = parse_list_to_dict(form.loads(from_env.headers))
        from_env_func_files = form.loads(from_env.func_files)
        synchronization_result = {}
        for to_env in form.envTo.data:
            to_env_data = UiProjectEnv.get_first(project_id=form.projectId.data, env=to_env)

            # 变量
            variables = parse_list_to_dict(to_env_data.loads(to_env_data.variables))
            for key, value in from_env_variable.items():
                variables.setdefault(key, value)

            # 头部信息
            headers = parse_list_to_dict(to_env_data.loads(to_env_data.headers))
            for key, value in from_env_headers.items():
                headers.setdefault(key, value)

            # 函数文件
            func_files = to_env_data.loads(to_env_data.func_files)
            func_files.extend(from_env_func_files)

            to_env_data.update({
                'variables': form.dumps(parse_dict_to_list(variables)),
                'headers': form.dumps(parse_dict_to_list(headers)),
                'func_files': form.dumps(func_files),
            })
            synchronization_result[to_env] = to_env_data.to_dict()
        return restful.success('同步成功', data=synchronization_result)
    return restful.fail(form.get_error())


class ProjectEnvView(BaseMethodView):
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
            env = UiProjectEnv().create(form.data, 'variables', 'headers', 'func_files')
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
            return restful.success(f'环境保存成功', form.env_data.to_dict())
        return restful.fail(msg=form.get_error())


ui_test.add_url_rule('/project', view_func=ProjectView.as_view('ui_project'))
ui_test.add_url_rule('/project/env', view_func=ProjectEnvView.as_view('ui_project_env'))
