# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.busines import ProjectBusiness, ProjectEnvBusiness
from app.web_ui_test.blueprint import ui_test
from app.web_ui_test.models.project import WebUiProject as Project, WebUiProjectEnv as ProjectEnv
from app.web_ui_test.models.suite import WebUiCaseSuite as CaseSuite
from app.web_ui_test.forms.project import (
    AddUiProjectForm, EditUiProjectForm, FindUiProjectForm, DeleteUiProjectForm, GetUiProjectByIdForm,
    EditEnv, AddEnv, FindEnvForm, SynchronizationEnvForm
)


@ui_test.login_get("/project/list")
def ui_get_project_list():
    """ 查找项目列表 """
    form = FindUiProjectForm().do_validate()
    return app.restful.success(data=Project.make_pagination(form))


@ui_test.login_put("/project/sort")
def ui_change_project_sort():
    """ 更新服务的排序 """
    Project.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
    return app.restful.success(msg="修改排序成功")


@ui_test.login_get("/project")
def ui_get_project():
    """ 获取项目 """
    form = GetUiProjectByIdForm().do_validate()
    return app.restful.success(data=form.project.to_dict())


@ui_test.login_post("/project")
def ui_add_project():
    """ 新增项目 """
    form = AddUiProjectForm().do_validate()
    project = ProjectBusiness.post(form, Project, ProjectEnv, CaseSuite)
    return app.restful.success(f"项目【{form.name.data}】新建成功", project.to_dict())


@ui_test.login_put("/project")
def ui_change_project():
    """ 修改项目 """
    form = EditUiProjectForm().do_validate()
    form.project.update(form.data)
    return app.restful.success(f"项目【{form.name.data}】修改成功", form.project.to_dict())


@ui_test.login_delete("/project")
def ui_delete_project():
    """ 删除项目 """
    form = DeleteUiProjectForm().do_validate()
    form.project.delete_current_and_env()
    return app.restful.success(msg=f"项目【{form.project.name}】删除成功")


@ui_test.login_post("/project/env/synchronization")
def ui_synchronization_project_env():
    """ 同步环境数据 """
    form = SynchronizationEnvForm().do_validate()
    from_env = ProjectEnv.get_first(project_id=form.projectId.data, env_id=form.envFrom.data)
    synchronization_result = ProjectEnv.synchronization(from_env, form.envTo.data, ["variables"])
    return app.restful.success("同步成功", data=synchronization_result)


@ui_test.login_get("/project/env")
def ui_get_project_env():
    """ 获取项目环境 """
    form = FindEnvForm().do_validate()
    return app.restful.success(data=form.env_data.to_dict())


@ui_test.login_post("/project/env")
def ui_add_project_env():
    """ 新增项目环境 """
    form = AddEnv().do_validate()
    env = ProjectEnv().create(form.data)
    return app.restful.success(f"环境新建成功", env.to_dict())


@ui_test.login_put("/project/env")
def ui_change_project_env():
    """ 修改项目环境 """
    form = EditEnv().do_validate()
    ProjectEnvBusiness.put(form, ProjectEnv, ["variables"])
    return app.restful.success(f"环境保存成功", form.env_data.to_dict())
