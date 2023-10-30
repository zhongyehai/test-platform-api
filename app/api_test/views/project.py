# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.api_test.blueprint import api_test
from app.busines import ProjectBusiness, ProjectEnvBusiness
from app.api_test.models.project import ApiProject as Project, ApiProjectEnv as ProjectEnv
from app.api_test.models.suite import ApiCaseSuite as CaseSuite
from app.api_test.forms.project import (
    AddProjectForm, EditProjectForm, FindProjectForm, DeleteProjectForm, GetProjectByIdForm,
    EditEnv, AddEnv, FindEnvForm, SynchronizationEnvForm
)


@api_test.login_get("/project/list")
def api_get_project_list():
    """ 获取服务列表 """
    form = FindProjectForm().do_validate()
    return app.restful.success(data=Project.make_pagination(form))


@api_test.login_put("/project/sort")
def api_change_project_sort():
    """ 更新服务的排序 """
    Project.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
    return app.restful.success(msg="修改排序成功")


@api_test.login_get("/project")
def api_get_project():
    """ 获取服务 """
    form = GetProjectByIdForm().do_validate()
    return app.restful.success(data=form.project.to_dict())


@api_test.login_post("/project")
def api_add_project():
    """ 新增服务 """
    form = AddProjectForm().do_validate()
    project = ProjectBusiness.post(form, Project, ProjectEnv, CaseSuite)
    return app.restful.success(f"服务【{form.name.data}】新建成功", project.to_dict())


@api_test.login_put("/project")
def api_change_project():
    """ 修改服务 """
    form = EditProjectForm().do_validate()
    form.project.update(form.data)
    return app.restful.success(f"服务【{form.name.data}】修改成功", form.project.to_dict())


@api_test.login_delete("/project")
def api_delete_project():
    """ 删除服务 """
    form = DeleteProjectForm().do_validate()
    form.project.delete_current_and_env()
    return app.restful.success(msg=f"服务【{form.project.name}】删除成功")


@api_test.login_post("/project/env/synchronization")
def api_synchronization_project_env():
    """ 同步环境数据 """
    form = SynchronizationEnvForm().do_validate()
    from_env = ProjectEnv.get_first(project_id=form.projectId.data, env_id=form.envFrom.data)
    synchronization_result = ProjectEnv.synchronization(from_env, form.envTo.data, ["variables", "headers"])
    return app.restful.success("同步成功", data=synchronization_result)


@api_test.login_get("/project/env")
def api_get_project_env():
    """ 获取服务环境 """
    form = FindEnvForm().do_validate()
    return app.restful.success(data=form.env_data.to_dict())


@api_test.login_post("/project/env")
def api_add_project_env():
    """ 新增服务环境 """
    form = AddEnv().do_validate()
    env = ProjectEnv().create(form.data)
    return app.restful.success(f"环境新建成功", env.to_dict())


@api_test.login_put("/project/env")
def api_change_project_env():
    """ 修改服务环境 """
    form = EditEnv().do_validate()
    ProjectEnvBusiness.put(form, ProjectEnv, ["variables", "headers"])
    return app.restful.success(f"环境修改成功", form.env_data.to_dict())
