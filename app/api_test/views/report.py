# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.baseView import LoginRequiredView, NotLoginView
from utils.report.report import render_html_report
from app.api_test.blueprint import api_test
from app.api_test.models.report import ApiReport as Report
from app.assist.models.hits import Hits
from app.api_test.forms.report import GetReportForm, DownloadReportForm, FindReportForm, GetReportDetailForm, DeleteReportForm
from utils.util.fileUtil import FileUtil
from utils.view.required import login_required


class ApiDownloadReportView(LoginRequiredView):
    def get(self):
        """ 报告下载 """
        form = DownloadReportForm().do_validate()
        return app.restful.success(data=render_html_report(form.report_content))


class ApiGetReportListView(LoginRequiredView):
    def get(self):
        """ 报告列表 """
        form = FindReportForm().do_validate()
        return app.restful.success(data=Report.make_pagination(form))


class ApiReportDetailView(NotLoginView):
    def get(self):
        """ 获取报告详情 """
        form = GetReportDetailForm().do_validate()
        return app.restful.success("获取成功", data=form.report_content)


class ApiReportView(LoginRequiredView):

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


api_test.add_url_rule("/report", view_func=ApiReportView.as_view("ApiReportView"))
api_test.add_url_rule("/report/detail", view_func=ApiReportDetailView.as_view("ApiReportDetailView"))
api_test.add_url_rule("/report/list", view_func=ApiGetReportListView.as_view("ApiGetReportListView"))
api_test.add_url_rule("/report/download", view_func=ApiDownloadReportView.as_view("ApiDownloadReportView"))
