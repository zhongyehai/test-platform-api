# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.baseView import LoginRequiredView
from app.busines import ProjectBusiness, ProjectEnvBusiness
from app.app_ui_test.blueprint import app_ui_test
from app.app_ui_test.models.project import AppUiProject as Project, AppUiProjectEnv as ProjectEnv
from app.app_ui_test.models.caseSet import AppUiCaseSet as CaseSet
from app.app_ui_test.forms.project import (
    AddUiProjectForm, EditUiProjectForm, FindUiProjectForm, DeleteUiProjectForm, GetUiProjectByIdForm,
    EditEnv, AddEnv, FindEnvForm, SynchronizationEnvForm
)


class AppUiProjectAllView(LoginRequiredView):

    def get(self):
        """ 获取所有项目列表 """
        return app.restful.success(data=[project.to_dict() for project in Project.get_all()])


class AppUiProjectListView(LoginRequiredView):

    def get(self):
        """ 查找项目列表 """
        form = FindUiProjectForm().do_validate()
        return app.restful.success(data=Project.make_pagination(form))


class AppUiProjectChangeSortView(LoginRequiredView):

    def put(self):
        """ 更新服务的排序 """
        Project.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class AppProjectView(LoginRequiredView):

    def get(self):
        """ 获取项目 """
        form = GetUiProjectByIdForm().do_validate()
        return app.restful.success(data=form.project.to_dict())

    def post(self):
        """ 新增项目 """
        form = AddUiProjectForm().do_validate()
        project = ProjectBusiness.post(form, Project, ProjectEnv, CaseSet)
        return app.restful.success(f"项目【{form.name.data}】新建成功", project.to_dict())

    def put(self):
        """ 修改项目 """
        form = EditUiProjectForm().do_validate()
        form.project.update(form.data)
        return app.restful.success(f"项目【{form.name.data}】修改成功", form.project.to_dict())

    def delete(self):
        """ 删除项目 """
        form = DeleteUiProjectForm().do_validate()
        form.project.delete_current_and_env()
        return app.restful.success(msg=f"项目【{form.project.name}】删除成功")


class AppUiProjectEnvSynchronizationView(LoginRequiredView):

    def post(self):
        """ 同步环境数据 """
        form = SynchronizationEnvForm().do_validate()
        from_env = ProjectEnv.get_first(project_id=form.projectId.data, env=form.envFrom.data)
        synchronization_result = ProjectEnv.synchronization(from_env, form.envTo.data, ["variables"])
        return app.restful.success("同步成功", data=synchronization_result)


class AppUiProjectEnvView(LoginRequiredView):

    def get(self):
        """ 获取项目环境 """
        form = FindEnvForm().do_validate()
        return app.restful.success(data=form.env_data.to_dict())

    def post(self):
        """ 新增项目环境 """
        form = AddEnv().do_validate()
        env = ProjectEnv().create(form.data)
        return app.restful.success(f"环境新建成功", env.to_dict())

    def put(self):
        """ 修改项目环境 """
        form = EditEnv().do_validate()
        ProjectEnvBusiness.put(form, ProjectEnv, ["variables"])
        return app.restful.success(f"环境保存成功", form.env_data.to_dict())


app_ui_test.add_url_rule("/project", view_func=AppProjectView.as_view("AppProjectView"))
app_ui_test.add_url_rule("/project/env", view_func=AppUiProjectEnvView.as_view("AppUiProjectEnvView"))
app_ui_test.add_url_rule("/project/all", view_func=AppUiProjectAllView.as_view("AppUiProjectAllView"))
app_ui_test.add_url_rule("/project/list", view_func=AppUiProjectListView.as_view("AppUiProjectListView"))
app_ui_test.add_url_rule("/project/sort", view_func=AppUiProjectChangeSortView.as_view("AppUiProjectChangeSortView"))
app_ui_test.add_url_rule("/project/env/synchronization",
                         view_func=AppUiProjectEnvSynchronizationView.as_view("AppUiProjectEnvSynchronizationView"))
