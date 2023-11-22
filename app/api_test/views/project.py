# -*- coding: utf-8 -*-
from flask import current_app as app

from ...api_test.blueprint import api_test
from ...base_form import ChangeSortForm
from ..model_factory import ApiProject as Project, ApiProjectEnv as ProjectEnv, ApiCaseSuite as CaseSuite
from ...config.model_factory import RunEnv
from ..forms.project import (
    AddProjectForm, EditProjectForm, DeleteProjectForm, GetProjectForm, EditEnv, GetEnvForm, SynchronizationEnvForm,
    GetProjectListForm
)


@api_test.login_get("/project/list")
def api_get_project_list():
    """ 获取服务列表 """
    form = GetProjectListForm()
    if form.detail:
        get_filed = [Project.id, Project.name, Project.swagger, Project.last_pull_status, Project.business_id,
                     Project.manager, Project.update_user]
    else:
        get_filed = [Project.id, Project.name, Project.business_id]
    return app.restful.get_success(Project.make_pagination(form, get_filed=get_filed))


@api_test.login_put("/project/sort")
def api_change_project_sort():
    """ 更新服务的排序 """
    form = ChangeSortForm()
    Project.change_sort(**form.model_dump())
    return app.restful.change_success()


@api_test.login_get("/project")
def api_get_project():
    """ 获取服务 """
    form = GetProjectForm()
    return app.restful.get_success(form.project.to_dict())


@api_test.login_post("/project")
def api_add_project():
    """ 新增服务 """
    form = AddProjectForm()
    Project.add_project(form, ProjectEnv, RunEnv, CaseSuite)
    return app.restful.add_success()


@api_test.login_put("/project")
def api_change_project():
    """ 修改服务 """
    form = EditProjectForm()
    Project.query.filter(Project.id == form.id).update(form.model_dump())
    return app.restful.change_success()


@api_test.login_delete("/project")
def api_delete_project():
    """ 删除服务 """
    form = DeleteProjectForm()
    Project.delete_by_id(form.id)
    return app.restful.delete_success()


@api_test.login_get("/project/env")
def api_get_project_env():
    """ 获取服务环境 """
    form = GetEnvForm()
    return app.restful.get_success(form.env_data.to_dict())


@api_test.login_put("/project/env")
def api_change_project_env():
    """ 修改服务环境 """
    form = EditEnv()
    ProjectEnv.change_env(form)
    return app.restful.change_success()


@api_test.login_post("/project/env/synchronization")
def api_synchronization_project_env():
    """ 同步环境数据 """
    form = SynchronizationEnvForm()
    ProjectEnv.synchronization(form.env_from_data, form.env_to)
    return app.restful.synchronize_success()
