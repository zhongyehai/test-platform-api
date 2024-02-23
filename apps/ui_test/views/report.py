# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import ui_test
from ..model_factory import WebUiReport as Report, WebUiReportStep as ReportStep, WebUiReportCase as ReportCase
from ..forms.report import GetReportForm, GetReportListForm, DeleteReportForm, GetReportCaseForm, \
    GetReportCaseListForm, GetReportStepForm, GetReportStepListForm, GetReportStatusForm, GetReportShowIdForm, \
    GetReportStepImgForm
from utils.util.file_util import FileUtil


@ui_test.login_get("/report/list")
def ui_get_report_list():
    """ 报告列表 """
    form = GetReportListForm()
    if form.detail:
        get_filed = [Report.id, Report.name, Report.create_time, Report.trigger_type, Report.env, Report.is_passed,
                     Report.process, Report.status, Report.create_user, Report.project_id, Report.trigger_id,
                     Report.run_type]
    else:
        get_filed = Report.get_simple_filed_list()
    return app.restful.get_success(Report.make_pagination(form, get_filed=get_filed))


@ui_test.get("/report/status")
def ui_get_report_status():
    """ 根据运行id获取当次报告是否全部生成 """
    form = GetReportStatusForm()
    return app.restful.get_success(
        Report.select_is_all_status_by_batch_id(form.batch_id, [form.process, form.status]))


@ui_test.get("/report/show-id")
def ui_get_report_show_id():
    """ 根据运行id获取当次要打开的报告 """
    form = GetReportShowIdForm()
    return app.restful.get_success(Report.select_show_report_id(form.batch_id))


@ui_test.get("/report")
def ui_get_report():
    """ 获取测试报告 """
    form = GetReportForm()
    return app.restful.get_success(form.report.to_dict())


@ui_test.login_delete("/report")
def ui_delete_report():
    """ 删除测试报告 """
    form = DeleteReportForm()
    Report.batch_delete_report(form.report_id_list)
    FileUtil.delete_report_img_by_report_id(form.report_id_list, 'ui')
    return app.restful.delete_success()


@ui_test.get("/report/case-list")
def ui_get_report_case_list():
    """ 报告的用例列表 """
    form = GetReportCaseListForm()
    case_list = ReportCase.get_resport_case_list(form.report_id, form.detail)
    return app.restful.get_success(case_list)


@ui_test.get("/report/case")
def ui_get_report_case():
    """ 报告的用例数据 """
    form = GetReportCaseForm()
    return app.restful.get_success(form.report_case.to_dict())


@ui_test.get("/report/step-list")
def ui_get_report_step_list():
    """ 报告的步骤列表 """
    form = GetReportStepListForm()
    step_list = ReportStep.get_resport_step_list(form.report_case_id, form.detail)
    return app.restful.get_success(step_list)


@ui_test.get("/report/step")
def ui_get_report_step():
    """ 报告的步骤数据 """
    form = GetReportStepForm()
    return app.restful.get_success(form.report_step.to_dict())


@ui_test.get("/report/step-img")
def ui_get_report_step_img():
    """ 报告的步骤截图 """
    form = GetReportStepImgForm()
    data = FileUtil.get_report_step_img(form.report_id, form.report_step_id, form.img_type, 'ui')
    return app.restful.get_success({"data": data, "total": 1 if data else 0})
