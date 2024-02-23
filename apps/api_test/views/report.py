# -*- coding: utf-8 -*-
from flask import current_app as app

from utils.client.parse_model import StepModel
from ..blueprint import api_test
from ..model_factory import ApiReport as Report, ApiReportStep as ReportStep, ApiReportCase as ReportCase, \
    ApiMsg, ApiCaseSuite as CaseSuite, ApiCase as Case, ApiStep as Step
from ..forms.report import GetReportForm, GetReportListForm, DeleteReportForm, GetReportCaseForm, \
    GetReportCaseListForm, GetReportStepForm, GetReportStepListForm, GetReportStatusForm, GetReportShowIdForm
from ...enums import ApiCaseSuiteTypeEnum


@api_test.login_get("/report/list")
def api_get_report_list():
    """ 报告列表 """
    form = GetReportListForm()
    if form.detail:
        get_filed = [Report.id, Report.name, Report.create_time, Report.trigger_type, Report.env, Report.is_passed,
                     Report.process, Report.status, Report.create_user, Report.project_id, Report.trigger_id,
                     Report.run_type]
    else:
        get_filed = Report.get_simple_filed_list()
    return app.restful.get_success(Report.make_pagination(form, get_filed=get_filed))


@api_test.get("/report/status")
def api_get_report_status():
    """ 根据运行id获取当次报告是否全部生成 """
    form = GetReportStatusForm()
    return app.restful.get_success(
        Report.select_is_all_status_by_batch_id(form.batch_id, [form.process, form.status]))


@api_test.get("/report/show-id")
def api_get_report_show_id():
    """ 根据运行id获取当次要打开的报告 """
    form = GetReportShowIdForm()
    return app.restful.get_success(Report.select_show_report_id(form.batch_id))


@api_test.post("/report/as-case")
def api_save_report_as_case():
    """ 保存报告中的接口为用例（仅报告运行类型为接口使用） """
    form = GetReportStepForm()
    report_step = form.report_step
    api = ApiMsg.get_first(id=report_step.element_id)
    case_suite = CaseSuite.get_first(project_id=api.project_id, suite_type=ApiCaseSuiteTypeEnum.base.api)
    case = Case.model_create_and_get({"name": report_step.name, "desc": report_step.name, "suite_id": case_suite.id})
    Step.model_create({"name": report_step.name, "case_id": case.id, "api_id": api.id, **api.to_dict()})
    return app.restful.add_success()


@api_test.get("/report")
def api_get_report():
    """ 获取测试报告 """
    form = GetReportForm()
    return app.restful.get_success(form.report.to_dict())


@api_test.login_delete("/report")
def api_delete_report():
    """ 删除测试报告主数据 """
    form = DeleteReportForm()
    Report.batch_delete_report(form.report_id_list)
    return app.restful.delete_success()


@api_test.get("/report/case-list")
def api_get_report_case_list():
    """ 报告的用例列表 """
    form = GetReportCaseListForm()
    case_list = ReportCase.get_resport_case_list(form.report_id, form.detail)
    return app.restful.get_success(case_list)


@api_test.get("/report/case")
def api_get_report_case():
    """ 报告的用例数据 """
    form = GetReportCaseForm()
    return app.restful.get_success(form.report_case.to_dict())


@api_test.get("/report/step-list")
def api_get_report_step_list():
    """ 报告的步骤列表 """
    form = GetReportStepListForm()
    step_list = ReportStep.get_resport_step_list(form.report_case_id, form.detail)
    return app.restful.get_success(step_list)


@api_test.get("/report/step")
def api_get_report_step():
    """ 报告的步骤数据 """
    form = GetReportStepForm()
    return app.restful.get_success(form.report_step.to_dict())
