# -*- coding: utf-8 -*-
from flask import current_app as app, request

from ...base_form import ChangeSortForm
from ..blueprint import ui_test
from ..model_factory import WebUiProject as Project, WebUiProjectEnv as ProjectEnv, WebUiCaseSuite as CaseSuite
from ...config.model_factory import RunEnv
from ..forms.project import (
    AddProjectForm, EditProjectForm, GetProjectListForm, DeleteProjectForm, GetProjectForm,
    EditEnv, GetEnvForm, SynchronizationEnvForm
)


@ui_test.login_get("/project/list")
def ui_get_project_list():
    """ 查找项目列表 """
    form = GetProjectListForm()
    if form.detail:
        get_filed = [Project.id, Project.name, Project.business_id, Project.manager, Project.update_user]
    else:
        get_filed = [Project.id, Project.name, Project.business_id]
    return app.restful.get_success(Project.make_pagination(form, get_filed=get_filed))


@ui_test.login_put("/project/sort")
def ui_change_project_sort():
    """ 更新服务的排序 """
    form = ChangeSortForm()
    Project.change_sort(**form.model_dump())
    return app.restful.change_success()


@ui_test.login_get("/project")
def ui_get_project():
    """ 获取项目 """
    form = GetProjectForm()
    return app.restful.get_success(form.project.to_dict())


@ui_test.login_post("/project")
def ui_add_project():
    """ 新增项目 """
    form = AddProjectForm()
    Project.add_project(form, ProjectEnv, RunEnv, CaseSuite)
    return app.restful.add_success()


@ui_test.login_put("/project")
def ui_change_project():
    """ 修改项目 """
    form = EditProjectForm()
    Project.query.filter(Project.id == form.id).update(form.model_dump())
    return app.restful.change_success()


@ui_test.login_delete("/project")
def ui_delete_project():
    """ 删除项目 """
    form = DeleteProjectForm()
    Project.delete_by_id(form.id)
    return app.restful.delete_success()


@ui_test.login_get("/project/env")
def ui_get_project_env():
    """ 获取项目环境 """
    form = GetEnvForm()
    return app.restful.get_success(form.env_data.to_dict())


@ui_test.login_put("/project/env")
def ui_change_project_env():
    """ 修改项目环境 """
    form = EditEnv()
    ProjectEnv.change_env(form)
    return app.restful.change_success()


@ui_test.login_post("/project/env/synchronization")
def ui_synchronization_project_env():
    """ 同步环境数据 """
    form = SynchronizationEnvForm()
    ProjectEnv.synchronization(form.env_from_data, form.env_to)
    return app.restful.synchronize_success()
