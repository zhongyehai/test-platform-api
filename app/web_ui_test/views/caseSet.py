# -*- coding: utf-8 -*-
from flask import request, g, current_app as app

from app.baseView import LoginRequiredView
from app.busines import RunCaseBusiness
from app.web_ui_test.models.case import WebUiCase as Case
from app.web_ui_test.models.report import WebUiReport as Report
from app.web_ui_test.blueprint import web_ui_test
from app.web_ui_test.models.caseSet import WebUiCaseSet as CaseSet
from app.web_ui_test.forms.caseSet import AddCaseSetForm, EditCaseSetForm, FindCaseSet, GetCaseSetEditForm, \
    DeleteCaseSetForm, RunCaseSetForm
from utils.client.runUiTest import RunCase


class WebUiGetCaseSetListView(LoginRequiredView):

    def get(self):
        """ 用例集list """
        form = FindCaseSet().do_validate()
        return app.restful.success(data=CaseSet.make_pagination(form))


class WebUiRunCaseSetView(LoginRequiredView):

    def post(self):
        """ 运行用例集下的用例 """
        form = RunCaseSetForm().do_validate()
        report_id = RunCaseBusiness.run(
            env=form.env.data,
            browser=form.browser.data,
            is_async=form.is_async.data,
            project_id=form.set.project_id,
            report_name=form.set.name,
            task_type="set",
            report_model=Report,
            case_id=form.set.get_run_case_id(Case),
            run_type="web_ui",
            run_func=RunCase
        )
        return app.restful.success(msg="触发执行成功，请等待执行完毕", data={"report_id": report_id})


class WebUiGetCaseSetTreeView(LoginRequiredView):

    def get(self):
        """ 获取当前服务下的用例集树 """
        set_list = [
            case_set.to_dict() for case_set in CaseSet.query.filter_by(
                project_id=int(request.args.get("project_id"))).order_by(CaseSet.parent.asc()).all()
        ]
        return app.restful.success(data=set_list)


class WebUiCaseSetView(LoginRequiredView):

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


web_ui_test.add_url_rule("/caseSet", view_func=WebUiCaseSetView.as_view("WebUiCaseSetView"))
web_ui_test.add_url_rule("/caseSet/run", view_func=WebUiRunCaseSetView.as_view("WebUiRunCaseSetView"))
web_ui_test.add_url_rule("/caseSet/tree", view_func=WebUiGetCaseSetTreeView.as_view("WebUiGetCaseSetTreeView"))
web_ui_test.add_url_rule("/caseSet/list", view_func=WebUiGetCaseSetListView.as_view("WebUiGetCaseSetListView"))
