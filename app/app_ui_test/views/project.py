# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.baseView import LoginRequiredView
from app.busines import ProjectBusiness, ProjectEnvBusiness
from app.app_ui_test.blueprint import app_ui_test
from app.app_ui_test.models.project import AppUiProject as Project, AppUiProjectEnv as ProjectEnv
from app.app_ui_test.models.caseSet import AppUiCaseSet as CaseSet
from app.app_ui_test.forms.project import (
    AddUiProjectForm, EditUiProjectForm, FindUiProjectForm, DeleteUiProjectForm, GetUiProjectByIdForm,
    EditEnv, AddEnv, FindEnvForm
)


class AppUiProjectAllView(LoginRequiredView):

    def get(self):
        """ 获取所有app列表 """
        return app.restful.success(data=[project.to_dict() for project in Project.get_all()])


class AppUiProjectListView(LoginRequiredView):

    def get(self):
        """ 查找app列表 """
        form = FindUiProjectForm().do_validate()
        return app.restful.success(data=Project.make_pagination(form))


class AppUiProjectChangeSortView(LoginRequiredView):

    def put(self):
        """ 更新app的排序 """
        Project.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class AppProjectView(LoginRequiredView):

    def get(self):
        """ 获取app """
        form = GetUiProjectByIdForm().do_validate()
        return app.restful.success(data=form.project.to_dict())

    def post(self):
        """ 新增app """
        form = AddUiProjectForm().do_validate()
        project = ProjectBusiness.post(form, Project, ProjectEnv, CaseSet)
        return app.restful.success(f"app【{form.name.data}】新建成功", project.to_dict())

    def put(self):
        """ 修改app """
        form = EditUiProjectForm().do_validate()
        form.project.update(form.data)
        return app.restful.success(f"app【{form.name.data}】修改成功", form.project.to_dict())

    def delete(self):
        """ 删除app """
        form = DeleteUiProjectForm().do_validate()
        form.project.delete_current_and_env()
        return app.restful.success(msg=f"app【{form.project.name}】删除成功")


class AppUiProjectEnvView(LoginRequiredView):

    def get(self):
        """ 获取app环境 """
        form = FindEnvForm().do_validate()
        return app.restful.success(data=form.env_data.to_dict())

    def post(self):
        """ 新增app环境 """
        form = AddEnv().do_validate()
        env = ProjectEnv().create(form.data)
        return app.restful.success(f"环境新建成功", env.to_dict())

    def put(self):
        """ 修改app环境 """
        form = EditEnv().do_validate()
        ProjectEnvBusiness.put(form, ProjectEnv, ["variables"])
        return app.restful.success(f"环境保存成功", form.env_data.to_dict())


app_ui_test.add_url_rule("/project", view_func=AppProjectView.as_view("AppProjectView"))
app_ui_test.add_url_rule("/project/env", view_func=AppUiProjectEnvView.as_view("AppUiProjectEnvView"))
app_ui_test.add_url_rule("/project/all", view_func=AppUiProjectAllView.as_view("AppUiProjectAllView"))
app_ui_test.add_url_rule("/project/list", view_func=AppUiProjectListView.as_view("AppUiProjectListView"))
app_ui_test.add_url_rule("/project/sort", view_func=AppUiProjectChangeSortView.as_view("AppUiProjectChangeSortView"))
