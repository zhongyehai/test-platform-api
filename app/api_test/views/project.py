# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.api_test.blueprint import api_test
from app.busines import ProjectBusiness, ProjectEnvBusiness
from app.api_test.models.project import ApiProject as Project, ApiProjectEnv as ProjectEnv
from app.api_test.models.caseSuite import ApiCaseSuite as CaseSuite
from app.api_test.forms.project import (
    AddProjectForm, EditProjectForm, FindProjectForm, DeleteProjectForm, GetProjectByIdForm,
    EditEnv, AddEnv, FindEnvForm, SynchronizationEnvForm
)
from app.baseView import LoginRequiredView


class ApiProjectListView(LoginRequiredView):

    def get(self):
        """ 获取服务列表 """
        form = FindProjectForm().do_validate()
        return app.restful.success(data=Project.make_pagination(form))


class ProjectChangeSortView(LoginRequiredView):

    def put(self):
        """ 更新服务的排序 """
        Project.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class ApiProjectView(LoginRequiredView):
    """ 服务管理 """

    def get(self):
        """ 获取服务 """
        form = GetProjectByIdForm().do_validate()
        return app.restful.success(data=form.project.to_dict())

    def post(self):
        """ 新增服务 """
        form = AddProjectForm().do_validate()
        project = ProjectBusiness.post(form, Project, ProjectEnv, CaseSuite)
        return app.restful.success(f"服务【{form.name.data}】新建成功", project.to_dict())

    def put(self):
        """ 修改服务 """
        form = EditProjectForm().do_validate()
        form.project.update(form.data)
        return app.restful.success(f"服务【{form.name.data}】修改成功", form.project.to_dict())

    def delete(self):
        """ 删除服务 """
        form = DeleteProjectForm().do_validate()
        form.project.delete_current_and_env()
        return app.restful.success(msg=f"服务【{form.project.name}】删除成功")


class ApiProjectEnvViewSynchronizationView(LoginRequiredView):

    def post(self):
        """ 同步环境数据 """
        form = SynchronizationEnvForm().do_validate()
        from_env = ProjectEnv.get_first(project_id=form.projectId.data, env_id=form.envFrom.data)
        synchronization_result = ProjectEnv.synchronization(from_env, form.envTo.data, ["variables", "headers"])
        return app.restful.success("同步成功", data=synchronization_result)


class ApiProjectEnvView(LoginRequiredView):
    """ 服务环境管理 """

    def get(self):
        """ 获取服务环境 """
        form = FindEnvForm().do_validate()
        return app.restful.success(data=form.env_data.to_dict())

    def post(self):
        """ 新增服务环境 """
        form = AddEnv().do_validate()
        env = ProjectEnv().create(form.data)
        return app.restful.success(f"环境新建成功", env.to_dict())

    def put(self):
        """ 修改服务环境 """
        form = EditEnv().do_validate()
        ProjectEnvBusiness.put(form, ProjectEnv, ["variables", "headers"])
        return app.restful.success(f"环境修改成功", form.env_data.to_dict())


api_test.add_url_rule("/project", view_func=ApiProjectView.as_view("ApiProjectView"))
api_test.add_url_rule("/project/list", view_func=ApiProjectListView.as_view("ApiProjectListView"))
api_test.add_url_rule("/project/sort", view_func=ProjectChangeSortView.as_view("ProjectChangeSortView"))
api_test.add_url_rule("/project/env", view_func=ApiProjectEnvView.as_view("ApiProjectEnvView"))
api_test.add_url_rule("/project/env/synchronization",
                      view_func=ApiProjectEnvViewSynchronizationView.as_view("ApiProjectEnvViewSynchronizationView"))
