# -*- coding: utf-8 -*-
from flask import request, current_app as app

from app.baseView import LoginRequiredView, NotLoginView
from utils.message.template import render_html_report
from app.app_ui_test.blueprint import app_ui_test
from app.app_ui_test.models.report import AppUiReport as Report
from app.app_ui_test.forms.report import GetReportForm, DownloadReportForm, FindReportForm, GetReportDetailForm, DeleteReportForm
from utils.util.fileUtil import FileUtil
from utils.view.required import login_required


class AppUiDownloadReportView(LoginRequiredView):

    def get(self):
        """ 报告下载 """
        form = DownloadReportForm().do_validate()
        return app.restful.success(data=render_html_report(form.report_content))


class AppUiReportListView(LoginRequiredView):

    def post(self):
        """ 报告列表 """
        form = FindReportForm().do_validate()
        return app.restful.success(data=Report.make_pagination(form))


class AppUiReportDetailView(NotLoginView):

    def get(self):
        """ 获取测试报告详情 """
        form = GetReportDetailForm().do_validate()
        return app.restful.success("获取成功", data=form.report_content)


class AppReportIsDoneView(NotLoginView):
    def get(self):
        """ 根据运行id获取当次报告是否全部生成 """
        batch_id, process, status = request.args["batch_id"], request.args.get("process", 1), request.args.get("status", 1)
        return app.restful.success(
            "获取成功",
            data=Report.select_is_all_status_by_batch_id(batch_id, [int(process), int(status)])
        )


class AppReportGetReportIdView(NotLoginView):
    def get(self):
        """ 根据运行id获取当次要打开的报告 """
        batch_id = request.args["batch_id"]
        return app.restful.success("获取成功", data=Report.select_show_report_id(batch_id))


class AppUiReportView(LoginRequiredView):

    def get(self):
        """ 获取测试报告 """
        form = GetReportForm().do_validate()
        return app.restful.success("获取成功", data=form.report.to_dict())

    @login_required
    def delete(self):
        """ 删除测试报告 """
        form = DeleteReportForm().do_validate()
        for report in form.report_list:
            report.delete()
            FileUtil.delete_file(report.report_path)
        return app.restful.success("删除成功")


app_ui_test.add_url_rule("/report", view_func=AppUiReportView.as_view("AppUiReportView"))
app_ui_test.add_url_rule("/report/list", view_func=AppUiReportListView.as_view("AppUiReportListView"))
app_ui_test.add_url_rule("/report/detail", view_func=AppUiReportDetailView.as_view("AppUiReportDetailView"))
app_ui_test.add_url_rule("/report/download", view_func=AppUiDownloadReportView.as_view("AppUiDownloadReportView"))
app_ui_test.add_url_rule("/report/status", view_func=AppReportIsDoneView.as_view("AppReportIsDoneView"))
app_ui_test.add_url_rule("/report/showId", view_func=AppReportGetReportIdView.as_view("AppReportGetReportIdView"))
