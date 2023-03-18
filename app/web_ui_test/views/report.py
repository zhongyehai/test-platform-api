# -*- coding: utf-8 -*-
from flask import request, current_app as app

from app.baseView import LoginRequiredView, NotLoginView
from utils.report.report import render_html_report
from app.web_ui_test.blueprint import web_ui_test
from app.web_ui_test.models.report import WebUiReport as Report
from app.web_ui_test.forms.report import GetReportForm, DownloadReportForm, FindReportForm, GetReportDetailForm, \
    DeleteReportForm
from utils.util.fileUtil import FileUtil
from utils.view.required import login_required


class WebUiDownloadReportView(LoginRequiredView):

    def get(self):
        """ 报告下载 """
        form = DownloadReportForm().do_validate()
        return app.restful.success(data=render_html_report(form.report_content))


class WebUiReportListView(LoginRequiredView):

    def get(self):
        """ 报告列表 """
        form = FindReportForm().do_validate()
        return app.restful.success(data=Report.make_pagination(form))


class WebUiReportDetailView(NotLoginView):

    def get(self):
        """ 获取报告详情 """
        form = GetReportDetailForm().do_validate()
        return app.restful.success("获取成功", data=form.report_content)


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
            report.delete()
            FileUtil.delete_file(report.report_path)
        return app.restful.success("删除成功")


web_ui_test.add_url_rule("/report", view_func=WebUiReportView.as_view("WebUiReportView"))
web_ui_test.add_url_rule("/report/list", view_func=WebUiReportListView.as_view("WebUiReportListView"))
web_ui_test.add_url_rule("/report/detail", view_func=WebUiReportDetailView.as_view("WebUiReportDetailView"))
web_ui_test.add_url_rule("/report/download", view_func=WebUiDownloadReportView.as_view("WebUiDownloadReportView"))
