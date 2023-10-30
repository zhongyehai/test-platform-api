# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.api_test.blueprint import api_test
from app.api_test.models.report import ApiReport as Report, ApiReportStep, ApiReportCase, ApiReport
from app.api_test.forms.report import GetReportForm, FindReportForm, DeleteReportForm, GetReportCaseForm, \
    GetReportCaseListForm, GetReportStepForm, GetReportStepListForm


@api_test.login_post("/report/list")
def api_get_report_list():
    """ 报告列表 """
    form = FindReportForm().do_validate()
    return app.restful.success(data=Report.make_pagination(form))


@api_test.get("/report/status")
def api_get_report_status():
    """ 根据运行id获取当次报告是否全部生成 """
    batch_id, process, status = request.args["batch_id"], request.args.get("process", 1), request.args.get("status",
                                                                                                           1)
    return app.restful.success(
        "获取成功",
        data=Report.select_is_all_status_by_batch_id(batch_id, [int(process), int(status)])
    )


@api_test.get("/report/showId")
def api_get_report_show_id():
    """ 根据运行id获取当次要打开的报告 """
    batch_id = request.args["batch_id"]
    return app.restful.success("获取成功", data=Report.select_show_report_id(batch_id))


@api_test.get("/report")
def api_get_report():
    """ 获取测试报告 """
    form = GetReportForm().do_validate()
    return app.restful.success("获取成功", data=form.report.to_dict())


@api_test.login_delete("/report")
def api_delete_report():
    """ 删除测试报告主数据 """
    form = DeleteReportForm().do_validate()
    ApiReport.batch_delete_report(form.report_id_list)
    return app.restful.success("删除成功")


@api_test.login_delete("/report/clear")
def api_clear_report():
    """ 清除测试报告 """
    ApiReport.batch_delete_report_case(ApiReportCase, ApiReportStep)
    return app.restful.success("清除成功")


@api_test.get("/report/case/list")
def api_get_report_case_list():
    """ 报告的用例列表 """
    form = GetReportCaseListForm().do_validate()
    case_list = ApiReportCase.get_case_list(form.report_id.data, form.get_summary.data)
    return app.restful.success(data=case_list)


@api_test.get("/report/case")
def api_get_report_case():
    """ 报告的用例数据 """
    form = GetReportCaseForm().do_validate()
    return app.restful.success(data=form.case_data.to_dict())


@api_test.get("/report/step/list")
def api_get_report_step_list():
    """ 报告的步骤列表 """
    form = GetReportStepListForm().do_validate()
    step_list = ApiReportStep.get_step_list(form.report_case_id.data, form.get_summary.data)
    return app.restful.success(data=step_list)


@api_test.get("/report/step")
def api_get_report_step():
    """ 报告的步骤数据 """
    form = GetReportStepForm().do_validate()
    return app.restful.success(data=form.step_data.to_dict())
