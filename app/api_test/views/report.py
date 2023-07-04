# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.baseView import LoginRequiredView, NotLoginView
from app.api_test.blueprint import api_test
from app.api_test.models.report import ApiReport as Report, ApiReportStep, ApiReportCase
from app.api_test.forms.report import GetReportForm, FindReportForm, DeleteReportForm, GetReportCaseForm, \
    GetReportCaseListForm, GetReportStepForm, GetReportStepListForm
from utils.view.required import login_required


class ApiGetReportListView(LoginRequiredView):
    def post(self):
        """ 报告列表 """
        form = FindReportForm().do_validate()
        return app.restful.success(data=Report.make_pagination(form))


class ApiReportIsDoneView(NotLoginView):
    def get(self):
        """ 根据运行id获取当次报告是否全部生成 """
        batch_id, process, status = request.args["batch_id"], request.args.get("process", 1), request.args.get("status",
                                                                                                               1)
        return app.restful.success(
            "获取成功",
            data=Report.select_is_all_status_by_batch_id(batch_id, [int(process), int(status)])
        )


class ApiReportGetReportIdView(NotLoginView):
    def get(self):
        """ 根据运行id获取当次要打开的报告 """
        batch_id = request.args["batch_id"]
        return app.restful.success("获取成功", data=Report.select_show_report_id(batch_id))


class ApiReportView(NotLoginView):

    def get(self):
        """ 获取测试报告 """
        form = GetReportForm().do_validate()
        return app.restful.success("获取成功", data=form.report.to_dict())

    @login_required
    def delete(self):
        """ 删除测试报告 """
        form = DeleteReportForm().do_validate()
        for report in form.report_list:
            ApiReportCase.delete_by_report(report.id)
            ApiReportStep.delete_by_report(report.id)
            report.delete()
        return app.restful.success("删除成功")


class ApiGetReportCaseListView(NotLoginView):
    def get(self):
        """ 报告的用例列表 """
        form = GetReportCaseListForm().do_validate()
        case_list = ApiReportCase.get_case_list(form.report_id.data, form.get_summary.data)
        return app.restful.success(data=case_list)


class ApiGetReportCCseView(NotLoginView):
    def get(self):
        """ 报告的用例数据 """
        form = GetReportCaseForm().do_validate()
        return app.restful.success(data=form.case_data.to_dict())


class ApiGetReportStepListView(NotLoginView):
    def get(self):
        """ 报告的步骤列表 """
        form = GetReportStepListForm().do_validate()
        step_list = ApiReportStep.get_step_list(form.report_case_id.data, form.get_summary.data)
        return app.restful.success(data=step_list)


class ApiGetReportStepView(NotLoginView):
    def get(self):
        """ 报告的步骤数据 """
        form = GetReportStepForm().do_validate()
        return app.restful.success(data=form.step_data.to_dict())


api_test.add_url_rule("/report", view_func=ApiReportView.as_view("ApiReportView"))
api_test.add_url_rule("/report/list", view_func=ApiGetReportListView.as_view("ApiGetReportListView"))
api_test.add_url_rule("/report/status", view_func=ApiReportIsDoneView.as_view("ApiReportIsDoneView"))
api_test.add_url_rule("/report/showId", view_func=ApiReportGetReportIdView.as_view("ApiReportGetReportIdView"))
api_test.add_url_rule("/report/case", view_func=ApiGetReportCCseView.as_view("ApiGetReportCCseView"))
api_test.add_url_rule("/report/case/list", view_func=ApiGetReportCaseListView.as_view("ApiGetReportCaseListView"))
api_test.add_url_rule("/report/step", view_func=ApiGetReportStepView.as_view("ApiGetReportStepView"))
api_test.add_url_rule("/report/step/list", view_func=ApiGetReportStepListView.as_view("ApiGetReportStepListView"))
