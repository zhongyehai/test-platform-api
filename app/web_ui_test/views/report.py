# -*- coding: utf-8 -*-
from flask import request, current_app as app

from app.baseView import LoginRequiredView, NotLoginView
from app.web_ui_test.blueprint import web_ui_test
from app.web_ui_test.models.report import WebUiReport as Report, WebUiReportStep, WebUiReportCase
from app.web_ui_test.forms.report import GetReportForm, FindReportForm, DeleteReportForm, GetReportCaseForm, \
    GetReportCaseListForm, GetReportStepForm, GetReportStepListForm
from utils.view.required import login_required


class WebUiReportListView(LoginRequiredView):

    def post(self):
        """ 报告列表 """
        form = FindReportForm().do_validate()
        return app.restful.success(data=Report.make_pagination(form))


class WebUiReportIsDoneView(NotLoginView):
    def get(self):
        """ 根据运行id获取当次报告是否全部生成 """
        batch_id, process, status = request.args["batch_id"], request.args.get("process", 1), request.args.get("status",
                                                                                                               1)
        return app.restful.success(
            "获取成功",
            data=Report.select_is_all_status_by_batch_id(batch_id, [int(process), int(status)])
        )


class WebUiReportGetReportIdView(NotLoginView):
    def get(self):
        """ 根据运行id获取当次要打开的报告 """
        batch_id = request.args["batch_id"]
        return app.restful.success("获取成功", data=Report.select_show_report_id(batch_id))


class WebUiReportView(LoginRequiredView):

    def get(self):
        """ 获取测试报告 """
        form = GetReportForm().do_validate()
        return app.restful.success("获取成功", data=form.report.to_dict())

    @login_required
    def delete(self):
        """ 删除测试报告 """
        form = DeleteReportForm().do_validate()
        for report in form.report_list:
            WebUiReportCase.delete_by_report(report.id)
            WebUiReportStep.delete_by_report(report.id)
            report.delete()
        return app.restful.success("删除成功")


class WebUiGetReportCaseListView(NotLoginView):
    def get(self):
        """ 报告的用例列表 """
        form = GetReportCaseListForm().do_validate()
        case_list = WebUiReportCase.get_case_list(form.report_id.data, form.get_summary.data)
        return app.restful.success(data=case_list)


class WebUiGetReportCaseView(NotLoginView):
    def get(self):
        """ 报告的用例数据 """
        form = GetReportCaseForm().do_validate()
        return app.restful.success(data=form.case_data.to_dict())


class WebUiGetReportStepListView(NotLoginView):
    def get(self):
        """ 报告的步骤列表 """
        form = GetReportStepListForm().do_validate()
        step_list = WebUiReportStep.get_step_list(form.report_case_id.data, form.get_summary.data)
        return app.restful.success(data=step_list)


class WebUiGetReportStepView(NotLoginView):
    def get(self):
        """ 报告的步骤数据 """
        form = GetReportStepForm().do_validate()
        return app.restful.success(data=form.step_data.to_dict())


web_ui_test.add_url_rule("/report", view_func=WebUiReportView.as_view("WebUiReportView"))
web_ui_test.add_url_rule("/report/list", view_func=WebUiReportListView.as_view("WebUiReportListView"))
web_ui_test.add_url_rule("/report/status", view_func=WebUiReportIsDoneView.as_view("WebUiReportIsDoneView"))
web_ui_test.add_url_rule("/report/showId", view_func=WebUiReportGetReportIdView.as_view("WebUiReportGetReportIdView"))
web_ui_test.add_url_rule("/report/step", view_func=WebUiGetReportCaseView.as_view("WebUiGetReportCaseView"))
web_ui_test.add_url_rule("/report/step/list",
                         view_func=WebUiGetReportCaseListView.as_view("WebUiGetReportCaseListView"))
web_ui_test.add_url_rule("/report/step", view_func=WebUiGetReportStepView.as_view("WebUiGetReportStepView"))
web_ui_test.add_url_rule("/report/step/list",
                         view_func=WebUiGetReportStepListView.as_view("WebUiGetReportStepListView"))
