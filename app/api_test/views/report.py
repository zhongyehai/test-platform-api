# -*- coding: utf-8 -*-
import os

from flask import current_app as app, request

from utils.report.report import render_html_report
from app.api_test import api_test
from app.baseModel import db
from app.api_test.models.report import ApiReport
from app.api_test.forms.report import GetReportForm, DownloadReportForm, DeleteReportForm, FindReportForm


@api_test.route('/report/download', methods=['GET'])
def api_download_report():
    """ 报告下载 """
    form = DownloadReportForm()
    if form.validate():
        return app.restful.success(data=render_html_report(form.report_content))
    return app.restful.fail(form.get_error())


@api_test.route('/report/list', methods=['GET'])
def api_report_list():
    """ 报告列表 """
    form = FindReportForm()
    if form.validate():
        return app.restful.success(data=ApiReport.make_pagination(form))
    return app.restful.fail(form.get_error())


@api_test.route('/report/done', methods=['GET'])
def api_report_is_done():
    """ 报告是否生成 """
    return app.restful.success(data=ApiReport.get_first(id=request.args.to_dict().get('id')).is_done)


@api_test.route('/report', methods=['GET'])
def api_get_report_not_login_required():
    """ 获取测试报告 """
    form = GetReportForm()
    if form.validate():
        with db.auto_commit():
            form.report.status = '已读'
        return app.restful.success('获取成功', data=form.report_content)
    return app.restful.fail(form.get_error())


@api_test.route('/report', methods=['DELETE'])
def api_delete_report():
    """ 删除测试报告 """
    form = DeleteReportForm()
    if form.validate():
        form.report.delete()
        if os.path.exists(form.report_path):
            os.remove(form.report_path)
        return app.restful.success('删除成功')
    return app.restful.fail(form.get_error())
