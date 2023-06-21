# -*- coding: utf-8 -*-
from flask import request, current_app as app

from app.baseView import LoginRequiredView, NotLoginView
from app.web_ui_test.blueprint import web_ui_test
from app.web_ui_test.models.report import WebUiReport as Report, WebUiReportStep
from app.web_ui_test.forms.report import GetReportForm, FindReportForm, DeleteReportForm, FindReportStepListForm, \
    FindReportStepForm
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
            WebUiReportStep.delete_by_report(report.id)
            report.delete()
        return app.restful.success("删除成功")


class WebUiGetReportStepListView(LoginRequiredView):
    def get(self):
        """ 报告的步骤列表 """
        form = FindReportStepListForm().do_validate()
        fields = ["id", "name", "process", "result"]
        query_data = WebUiReportStep.query.filter(WebUiReportStep.report_id == form.report_id.data).with_entities(
            WebUiReportStep.id, WebUiReportStep.name, WebUiReportStep.process, WebUiReportStep.result
        ).all()  # [(24, '登录', 'before', 'running')]
        return app.restful.success(data=[dict(zip(fields, d)) for d in query_data])


class WebUiGetReportStepView(NotLoginView):
    def get(self):
        """ 报告的步骤数据 """
        form = FindReportStepForm().do_validate()
        return app.restful.success(data=form.step_data.to_dict())


web_ui_test.add_url_rule("/report", view_func=WebUiReportView.as_view("WebUiReportView"))
web_ui_test.add_url_rule("/report/list", view_func=WebUiReportListView.as_view("WebUiReportListView"))
web_ui_test.add_url_rule("/report/status", view_func=WebUiReportIsDoneView.as_view("WebUiReportIsDoneView"))
web_ui_test.add_url_rule("/report/showId", view_func=WebUiReportGetReportIdView.as_view("WebUiReportGetReportIdView"))
web_ui_test.add_url_rule("/report/step", view_func=WebUiGetReportStepView.as_view("WebUiGetReportStepView"))
web_ui_test.add_url_rule("/report/step/list",
                         view_func=WebUiGetReportStepListView.as_view("WebUiGetReportStepListView"))
