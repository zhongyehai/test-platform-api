# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.busines import ProjectBusiness, ProjectEnvBusiness
from app.app_ui_test.blueprint import app_test
from app.app_ui_test.models.project import AppUiProject as Project, AppUiProjectEnv as ProjectEnv
from app.app_ui_test.models.suite import AppUiCaseSuite as CaseSuite
from app.app_ui_test.forms.project import (
    AddUiProjectForm, EditUiProjectForm, FindUiProjectForm, DeleteUiProjectForm, GetUiProjectByIdForm,
    EditEnv, AddEnv, FindEnvForm
)


@app_test.login_get("/project/list")
def app_get_project_list():
    """ 查找app列表 """
    form = FindUiProjectForm().do_validate()
    return app.restful.success(data=Project.make_pagination(form))


@app_test.login_put("/project/sort")
def app_change_project_sort():
    """ 更新app的排序 """
    Project.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
    return app.restful.success(msg="修改排序成功")


@app_test.login_get("/project")
def app_get_project():
    """ 获取app """
    form = GetUiProjectByIdForm().do_validate()
    return app.restful.success(data=form.project.to_dict())


@app_test.login_post("/project")
def app_add_project():
    """ 新增app """
    form = AddUiProjectForm().do_validate()
    project = ProjectBusiness.post(form, Project, ProjectEnv, CaseSuite)
    return app.restful.success(f"app【{form.name.data}】新建成功", project.to_dict())


@app_test.login_put("/project")
def app_change_project():
    """ 修改app """
    form = EditUiProjectForm().do_validate()
    form.project.update(form.data)
    return app.restful.success(f"app【{form.name.data}】修改成功", form.project.to_dict())


@app_test.login_delete("/project")
def app_delete_project():
    """ 删除app """
    form = DeleteUiProjectForm().do_validate()
    form.project.delete_current_and_env()
    return app.restful.success(msg=f"app【{form.project.name}】删除成功")


@app_test.login_get("/project/env")
def app_get_project_env():
    """ 获取app环境 """
    form = FindEnvForm().do_validate()
    return app.restful.success(data=form.env_data.to_dict())


@app_test.login_post("/project/env")
def app_add_project_env():
    """ 新增app环境 """
    form = AddEnv().do_validate()
    env = ProjectEnv().create(form.data)
    return app.restful.success(f"环境新建成功", env.to_dict())


@app_test.login_put("/project/env")
def app_change_project_env():
    """ 修改app环境 """
    form = EditEnv().do_validate()
    ProjectEnvBusiness.put(form, ProjectEnv, ["variables"])
    return app.restful.success(f"环境保存成功", form.env_data.to_dict())
