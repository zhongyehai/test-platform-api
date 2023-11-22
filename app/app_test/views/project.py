# -*- coding: utf-8 -*-
from flask import current_app as app, request

from ...base_form import ChangeSortForm
from ...app_test.blueprint import app_test
from ..model_factory import AppUiProject as Project, AppUiProjectEnv as ProjectEnv, AppUiCaseSuite as CaseSuite
from ...config.model_factory import RunEnv
from ..forms.project import (
    AddProjectForm, GetProjectListForm, DeleteProjectForm, GetProjectForm, EditProjectForm,
    EditEnv, GetEnvForm, SynchronizationEnvForm
)


@app_test.login_get("/project/list")
def app_get_project_list():
    """ 查找app列表 """
    form = GetProjectListForm()
    if form.detail:
        get_filed = [Project.id, Project.name, Project.business_id, Project.app_package, Project.manager,
                     Project.update_user]
    else:
        get_filed = [Project.id, Project.name, Project.business_id]
    return app.restful.get_success(Project.make_pagination(form, get_filed=get_filed))


@app_test.login_put("/project/sort")
def app_change_project_sort():
    """ 更新app的排序 """
    form = ChangeSortForm()
    Project.change_sort(**form.model_dump())
    return app.restful.change_success()


@app_test.login_get("/project")
def app_get_project():
    """ 获取app """
    form = GetProjectForm()
    return app.restful.get_success(data=form.project.to_dict())


@app_test.login_post("/project")
def app_add_project():
    """ 新增app """
    form = AddProjectForm()
    Project.add_project(form, ProjectEnv, RunEnv, CaseSuite)
    return app.restful.add_success()


@app_test.login_put("/project")
def app_change_project():
    """ 修改app """
    form = EditProjectForm()
    Project.query.filter(Project.id == form.id).update(form.model_dump())
    return app.restful.change_success()


@app_test.login_delete("/project")
def app_delete_project():
    """ 删除app """
    form = DeleteProjectForm()
    Project.delete_by_id(form.id)
    return app.restful.delete_success()


@app_test.login_get("/project/env")
def app_get_project_env():
    """ 获取app环境 """
    form = GetEnvForm()
    return app.restful.get_success(form.env_data.to_dict())


@app_test.login_put("/project/env")
def app_change_project_env():
    """ 修改app环境 """
    form = EditEnv()
    ProjectEnv.change_env(form)
    return app.restful.change_success()


@app_test.login_post("/project/env/synchronization")
def app_synchronization_project_env():
    """ 同步环境数据 """
    form = SynchronizationEnvForm()
    ProjectEnv.synchronization(form.env_from_data, form.env_to)
    return app.restful.synchronize_success()
