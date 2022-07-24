# -*- coding: utf-8 -*-

import os

from flask import request

from utils.report.report import render_html_report
from utils import restful
from utils.required import login_required
from app.ui_test import ui_test
from app.baseModel import db
from app.ui_test.models.report import UiReport as Report
from app.ui_test.forms.report import GetReportForm, DownloadReportForm, DeleteReportForm, FindReportForm


@ui_test.route('/report/download', methods=['GET'])
@login_required
def ui_download_report():
    """ 报告下载 """
    form = DownloadReportForm()
    if form.validate():
        return restful.success(data=render_html_report(form.report_content))
    return restful.fail(form.get_error())


@ui_test.route('/report/list', methods=['GET'])
@login_required
def ui_report_list():
    """ 报告列表 """
    form = FindReportForm()
    if form.validate():
        return restful.success(data=Report.make_pagination(form))
    return restful.fail(form.get_error())


@ui_test.route('/report/done', methods=['GET'])
@login_required
def ui_report_is_done():
    """ 报告是否生成 """
    return restful.success(data=Report.get_first(id=request.args.to_dict().get('id')).is_done)


@ui_test.route('/report', methods=['GET'])
def ui_get_report():
    """ 获取测试报告 """
    form = GetReportForm()
    if form.validate():
        with db.auto_commit():
            form.report.status = '已读'
        return restful.success('获取成功', data=form.report_content)
    return restful.fail(form.get_error())


@ui_test.route('/report', methods=['DELETE'])
@login_required
def ui_delete_report():
    """ 删除测试报告 """
    form = DeleteReportForm()
    if form.validate():
        form.report.delete()
        if os.path.exists(form.report_path):
            os.remove(form.report_path)
        return restful.success('删除成功')
    return restful.fail(form.get_error())
