# -*- coding: utf-8 -*-

from flask import current_app as app, request

from app.baseView import LoginRequiredView, NotLoginView
from utils.report.report import render_html_report
from app.api_test.blueprint import api_test
from app.api_test.models.report import ApiReport as Report
from app.api_test.forms.report import GetReportForm, DownloadReportForm, DeleteReportForm, FindReportForm
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


class ApiReportStatusView(LoginRequiredView):
    def get(self):
        """ 查询报告是否生成 """
        return app.restful.success(data=Report.get_first(id=request.args.to_dict().get('id')).status)


class ApiReportView(NotLoginView):

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


api_test.add_url_rule('/report', view_func=ApiReportView.as_view('ApiReportView'))
api_test.add_url_rule('/report/status', view_func=ApiReportStatusView.as_view('ApiReportStatusView'))
api_test.add_url_rule('/report/list', view_func=ApiGetReportListView.as_view('ApiGetReportListView'))
api_test.add_url_rule('/report/download', view_func=ApiDownloadReportView.as_view('ApiDownloadReportView'))
