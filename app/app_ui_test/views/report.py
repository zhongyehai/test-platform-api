# -*- coding: utf-8 -*-
from flask import request, current_app as app

from app.app_ui_test.blueprint import app_test
from app.app_ui_test.models.report import AppUiReport as Report, AppUiReportStep, AppUiReportCase, AppUiReport
from app.app_ui_test.forms.report import GetReportForm, FindReportForm, DeleteReportForm, GetReportCaseForm, \
    GetReportCaseListForm, GetReportStepForm, GetReportStepListForm, GetReportStepImgForm
from utils.util.fileUtil import FileUtil


@app_test.login_post("/report/list")
def app_get_report_list():
    """ 报告列表 """
    form = FindReportForm().do_validate()
    return app.restful.success(data=Report.make_pagination(form))


@app_test.get("/report/status")
def app_get_report_status():
    """ 根据运行id获取当次报告是否全部生成 """
    batch_id, process, status = request.args["batch_id"], request.args.get("process", 1), request.args.get("status",
                                                                                                           1)
    return app.restful.success(
        "获取成功",
        data=Report.select_is_all_status_by_batch_id(batch_id, [int(process), int(status)])
    )


@app_test.get("/report/showId")
def app_get_report_show_id():
    """ 根据运行id获取当次要打开的报告 """
    batch_id = request.args["batch_id"]
    return app.restful.success("获取成功", data=Report.select_show_report_id(batch_id))


@app_test.get("/report")
def app_get_report():
    """ 获取测试报告 """
    form = GetReportForm().do_validate()
    return app.restful.success("获取成功", data=form.report.to_dict())


@app_test.login_delete("/report")
def app_delete_report():
    """ 删除测试报告 """
    form = DeleteReportForm().do_validate()
    AppUiReport.batch_delete_report(form.report_id_list)
    FileUtil.delete_report_img_by_report_id(form.report_id_list, 'app')
    return app.restful.success("删除成功")


@app_test.login_delete("/report/clear")
def app_clear_report():
    """ 清除测试报告 """
    AppUiReport.batch_delete_report_case(AppUiReportCase, AppUiReportStep)
    return app.restful.success("清除成功")


@app_test.get("/report/case/list")
def app_get_report_case_list():
    """ 报告的用例列表 """
    form = GetReportCaseListForm().do_validate()
    case_list = AppUiReportCase.get_case_list(form.report_id.data, form.get_summary.data)
    return app.restful.success(data=case_list)


@app_test.get("/report/case")
def app_get_report_case():
    """ 报告的用例数据 """
    form = GetReportCaseForm().do_validate()
    return app.restful.success(data=form.case_data.to_dict())


@app_test.get("/report/step/list")
def app_get_report_step_list():
    """ 报告的步骤列表 """
    form = GetReportStepListForm().do_validate()
    step_list = AppUiReportStep.get_step_list(form.report_case_id.data, form.get_summary.data)
    return app.restful.success(data=step_list)


@app_test.get("/report/step")
def app_get_report_step():
    """ 报告的步骤数据 """
    form = GetReportStepForm().do_validate()
    return app.restful.success(data=form.step_data.to_dict())


@app_test.post("/report/step/img")
def app_get_report_step_img():
    """ 报告的步骤截图 """
    form = GetReportStepImgForm().do_validate()
    data = FileUtil.get_report_step_img(form.report_id.data, form.report_step_id.data, form.img_type.data, 'app')
    return app.restful.get_success({"data": data, "total": 1 if data else 0})
