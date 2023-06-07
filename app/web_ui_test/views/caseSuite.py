# -*- coding: utf-8 -*-
from flask import request, g, current_app as app

from app.baseView import LoginRequiredView
from app.busines import RunCaseBusiness, CaseSuiteBusiness
from app.web_ui_test.models.case import WebUiCase as Case
from app.web_ui_test.models.report import WebUiReport as Report
from app.web_ui_test.blueprint import web_ui_test
from app.web_ui_test.models.caseSuite import WebUiCaseSuite as CaseSuite
from app.web_ui_test.forms.caseSuite import AddCaseSuiteForm, EditCaseSuiteForm, FindCaseSuite, GetCaseSuiteForm, \
    DeleteCaseSuiteForm, RunCaseSuiteForm
from utils.client.runUiTest import RunCase


class WebUiGetCaseSuiteListView(LoginRequiredView):

    def post(self):
        """ 用例集list """
        form = FindCaseSuite().do_validate()
        return app.restful.success(data=CaseSuite.make_pagination(form))


class WebUiCaseSuiteUploadView(LoginRequiredView):

    def post(self):
        """ 导入用例集 """
        project_id, file = request.form.get("project_id"), request.files.get("file")
        if project_id is None:
            return app.restful.fail("服务必传")
        if file and file.filename.endswith("xmind"):
            upload_res = CaseSuiteBusiness.upload_case_suite(project_id, file, CaseSuite, Case)
            return app.restful.success("导入完成", upload_res)
        return app.restful.fail("文件格式错误")


class WebUiRunCaseSuiteView(LoginRequiredView):

    def post(self):
        """ 运行用例集下的用例 """
        form = RunCaseSuiteForm().do_validate()
        batch_id = Report.get_batch_id()
        for env_code in form.env_list.data:
            RunCaseBusiness.run(
                batch_id=batch_id,
                env_code=env_code,
                browser=form.browser.data,
                is_async=form.is_async.data,
                project_id=form.suite.project_id,
                report_name=form.suite.name,
                task_type="suite",
                report_model=Report,
                trigger_id=form.id.data,
                case_id=form.suite.get_run_case_id(Case),
                run_type="webUi",
                run_func=RunCase
            )
        return app.restful.success(msg="触发执行成功，请等待执行完毕", data={"batch_id": batch_id})


class WebUiCaseSuiteView(LoginRequiredView):

    def get(self):
        """ 获取用例集 """
        form = GetCaseSuiteForm().do_validate()
        return app.restful.success(data=form.suite.to_dict())

    def post(self):
        """ 新增用例集 """
        form = AddCaseSuiteForm().do_validate()
        form.num.data = CaseSuite.get_insert_num(project_id=form.project_id.data)
        new_suite = CaseSuite().create(form.data)
        return app.restful.success(f"用例集【{form.name.data}】创建成功", new_suite.to_dict())

    def put(self):
        """ 修改用例集 """
        form = EditCaseSuiteForm().do_validate()
        form.suite.update(form.data)
        if form.is_update_suite_type: form.suite.update_children_suite_type()
        return app.restful.success(f"用例集【{form.name.data}】修改成功", form.suite.to_dict())

    def delete(self):
        """ 删除用例集 """
        form = DeleteCaseSuiteForm().do_validate()
        form.suite.delete()
        return app.restful.success("删除成功")


web_ui_test.add_url_rule("/caseSuite", view_func=WebUiCaseSuiteView.as_view("WebUiCaseSuiteView"))
web_ui_test.add_url_rule("/caseSuite/run", view_func=WebUiRunCaseSuiteView.as_view("WebUiRunCaseSuiteView"))
web_ui_test.add_url_rule("/caseSuite/list", view_func=WebUiGetCaseSuiteListView.as_view("WebUiGetCaseSuiteListView"))
web_ui_test.add_url_rule("/caseSuite/upload", view_func=WebUiCaseSuiteUploadView.as_view("WebUiCaseSuiteUploadView"))
