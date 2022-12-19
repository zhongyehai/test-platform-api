# -*- coding: utf-8 -*-
from flask import request, current_app as app

from app.baseView import LoginRequiredView
from app.busines import RunCaseBusiness
from app.app_ui_test.models.case import AppUiCase as Case
from app.app_ui_test.models.report import AppUiReport as Report
from app.app_ui_test.blueprint import app_ui_test
from app.app_ui_test.models.caseSet import AppUiCaseSet as CaseSet
from app.app_ui_test.forms.caseSet import AddCaseSetForm, EditCaseSetForm, FindCaseSet, GetCaseSetEditForm, \
    DeleteCaseSetForm, RunCaseSetForm
from utils.client.runUiTest import RunCase


class AppUiGetCaseSetListView(LoginRequiredView):

    def get(self):
        """ 用例集list """
        form = FindCaseSet().do_validate()
        return app.restful.success(data=CaseSet.make_pagination(form))


class AppUiRunCaseSetView(LoginRequiredView):

    def post(self):
        """ 运行用例集下的用例 """
        form = RunCaseSetForm().do_validate()
        appium_config = RunCaseBusiness.get_appium_config(form.set.project_id, form)
        report_id = RunCaseBusiness.run(
            env=form.env.data,
            is_async=form.is_async.data,
            project_id=form.set.project_id,
            report_name=form.set.name,
            task_type="set",
            report_model=Report,
            case_id=form.set.get_run_case_id(Case),
            run_type="app",
            run_func=RunCase,
            appium_config=appium_config
        )
        return app.restful.success(msg="触发执行成功，请等待执行完毕", data={"report_id": report_id})


class AppUiGetCaseSetTreeView(LoginRequiredView):

    def get(self):
        """ 获取当前服务下的用例集树 """
        set_list = [
            case_set.to_dict() for case_set in CaseSet.query.filter_by(
                project_id=int(request.args.get("project_id"))).order_by(CaseSet.parent.asc()).all()
        ]
        return app.restful.success(data=set_list)


class AppUiCaseSetView(LoginRequiredView):

    def get(self):
        """ 获取用例集 """
        form = GetCaseSetEditForm().do_validate()
        return app.restful.success(data={"name": form.set.name, "num": form.set.num})

    def post(self):
        """ 新增用例集 """
        form = AddCaseSetForm().do_validate()
        form.num.data = CaseSet.get_insert_num(project_id=form.project_id.data)
        new_set = CaseSet().create(form.data)
        return app.restful.success(f"用例集【{form.name.data}】创建成功", new_set.to_dict())

    def put(self):
        """ 修改用例集 """
        form = EditCaseSetForm().do_validate()
        form.case_set.update(form.data)
        return app.restful.success(f"用例集【{form.name.data}】修改成功", form.case_set.to_dict())

    def delete(self):
        """ 删除用例集 """
        form = DeleteCaseSetForm().do_validate()
        form.case_set.delete()
        return app.restful.success("删除成功")


app_ui_test.add_url_rule("/caseSet", view_func=AppUiCaseSetView.as_view("AppUiCaseSetView"))
app_ui_test.add_url_rule("/caseSet/run", view_func=AppUiRunCaseSetView.as_view("AppUiRunCaseSetView"))
app_ui_test.add_url_rule("/caseSet/tree", view_func=AppUiGetCaseSetTreeView.as_view("AppUiGetCaseSetTreeView"))
app_ui_test.add_url_rule("/caseSet/list", view_func=AppUiGetCaseSetListView.as_view("AppUiGetCaseSetListView"))
