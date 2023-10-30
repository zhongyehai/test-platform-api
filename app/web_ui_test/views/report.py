# -*- coding: utf-8 -*-
from flask import request, current_app as app

from app.web_ui_test.blueprint import ui_test
from app.web_ui_test.models.report import WebUiReport as Report, WebUiReportStep, WebUiReportCase, WebUiReport
from app.web_ui_test.forms.report import GetReportForm, FindReportForm, DeleteReportForm, GetReportCaseForm, \
    GetReportCaseListForm, GetReportStepForm, GetReportStepListForm, GetReportStepImgForm
from utils.util.fileUtil import FileUtil


@ui_test.login_post("/report/list")
def ui_get_report_list():
    """ 报告列表 """
    form = FindReportForm().do_validate()
    return app.restful.success(data=Report.make_pagination(form))


@ui_test.get("/report/status")
def ui_get_report_status():
    """ 根据运行id获取当次报告是否全部生成 """
    batch_id, process, status = request.args["batch_id"], request.args.get("process", 1), request.args.get("status",
                                                                                                           1)
    return app.restful.success(
        "获取成功",
        data=Report.select_is_all_status_by_batch_id(batch_id, [int(process), int(status)])
    )


@ui_test.get("/report/showId")
def ui_get_report_show_id():
    """ 根据运行id获取当次要打开的报告 """
    batch_id = request.args["batch_id"]
    return app.restful.success("获取成功", data=Report.select_show_report_id(batch_id))


@ui_test.get("/report")
def ui_get_report():
    """ 获取测试报告 """
    form = GetReportForm().do_validate()
    return app.restful.success("获取成功", data=form.report.to_dict())


@ui_test.login_delete("/report")
def ui_delete_report():
    """ 删除测试报告 """
    form = DeleteReportForm().do_validate()
    WebUiReport.batch_delete_report(form.report_id_list)
    FileUtil.delete_report_img_by_report_id(form.report_id_list, 'ui')
    return app.restful.success("删除成功")


@ui_test.login_delete("/report/clear")
def ui_clear_report():
    """ 清除测试报告 """
    WebUiReport.batch_delete_report_case(WebUiReportCase, WebUiReportStep)
    return app.restful.success("清除成功")


@ui_test.get("/report/case/list")
def ui_get_report_case_list():
    """ 报告的用例列表 """
    form = GetReportCaseListForm().do_validate()
    case_list = WebUiReportCase.get_case_list(form.report_id.data, form.get_summary.data)
    return app.restful.success(data=case_list)


@ui_test.get("/report/case")
def ui_get_report_case():
    """ 报告的用例数据 """
    form = GetReportCaseForm().do_validate()
    return app.restful.success(data=form.case_data.to_dict())


@ui_test.get("/report/step/list")
def ui_get_report_step_list():
    """ 报告的步骤列表 """
    """ 报告的步骤列表 """
    form = GetReportStepListForm().do_validate()
    step_list = WebUiReportStep.get_step_list(form.report_case_id.data, form.get_summary.data)
    return app.restful.success(data=step_list)


@ui_test.get("/report/step")
def ui_get_report_step():
    """ 报告的步骤数据 """
    form = GetReportStepForm().do_validate()
    return app.restful.success(data=form.step_data.to_dict())


@ui_test.post("/report/step/img")
def ui_get_report_step_img():
    """ 报告的步骤截图 """
    form = GetReportStepImgForm().do_validate()
    data = FileUtil.get_report_step_img(form.report_id.data, form.report_step_id.data, form.img_type.data, 'ui')
    return app.restful.get_success({"data": data, "total": 1 if data else 0})
