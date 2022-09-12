# -*- coding: utf-8 -*-
import os

from flask import current_app as app, request

from app.baseView import LoginRequiredView, NotLoginView
from utils.report.report import render_html_report
from app.api_test import api_test
from app.baseModel import db
from app.api_test.models.report import ApiReport
from app.api_test.forms.report import GetReportForm, DownloadReportForm, DeleteReportForm, FindReportForm
from utils.required import login_required

ns = api_test.namespace("report", description="测试报告管理相关接口")


@ns.route('/download/')
class ApiDownloadReportView(LoginRequiredView):
    def get(self):
        """ 报告下载 """
        form = DownloadReportForm()
        if form.validate():
            return app.restful.success(data=render_html_report(form.report_content))
        return app.restful.fail(form.get_error())


@ns.route('/list/')
class ApiGetReportListView(LoginRequiredView):
    def get(self):
        """ 报告列表 """
        form = FindReportForm()
        if form.validate():
            return app.restful.success(data=ApiReport.make_pagination(form))
        return app.restful.fail(form.get_error())


@ns.route('/done/')
class ApiReportIsDoneView(LoginRequiredView):
    def get(self):
        """ 查询报告是否生成 """
        return app.restful.success(data=ApiReport.get_first(id=request.args.to_dict().get('id')).is_done)


@ns.route('/')
class ApiReportView(NotLoginView):

    def get(self):
        """ 获取测试报告 """
        form = GetReportForm()
        if form.validate():
            with db.auto_commit():
                form.report.status = '已读'
            return app.restful.success('获取成功', data=form.report_content)
        return app.restful.fail(form.get_error())

    @login_required
    def delete(self):
        """ 删除测试报告 """
        form = DeleteReportForm()
        if form.validate():
            form.report.delete()
            if os.path.exists(form.report_path):
                os.remove(form.report_path)
            return app.restful.success('删除成功')
        return app.restful.fail(form.get_error())
