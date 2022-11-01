# -*- coding: utf-8 -*-

from flask import request, current_app as app

from app.baseView import LoginRequiredView, NotLoginView
from utils.report.report import render_html_report
from app.web_ui_test.blueprint import web_ui_test
from app.web_ui_test.models.report import WebUiReport as Report
from app.web_ui_test.forms.report import GetReportForm, DownloadReportForm, DeleteReportForm, FindReportForm
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


class WebUiReportStatusView(LoginRequiredView):

    def get(self):
        """ 查询报告是否生成 """
        return app.restful.success(data=Report.get_first(id=request.args.to_dict().get('id')).status)


class WebUiReportView(NotLoginView):

    def get(self):
        """ 获取测试报告 """
        form = GetReportForm().do_validate()
        form.report.read()
        return app.restful.success('获取成功', data=form.report_content)

    @login_required
    def delete(self):
        """ 删除测试报告 """
        form = DeleteReportForm().do_validate()
        form.report.delete()
        FileUtil.delete_file(form.report_path)
        return app.restful.success('删除成功')


web_ui_test.add_url_rule('/report', view_func=WebUiReportView.as_view('WebUiReportView'))
web_ui_test.add_url_rule('/report/status', view_func=WebUiReportStatusView.as_view('WebUiReportStatusView'))
web_ui_test.add_url_rule('/report/list', view_func=WebUiReportListView.as_view('WebUiReportListView'))
web_ui_test.add_url_rule('/report/download', view_func=WebUiDownloadReportView.as_view('WebUiDownloadReportView'))
