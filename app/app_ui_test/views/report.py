# -*- coding: utf-8 -*-
from flask import request, current_app as app

from app.baseView import LoginRequiredView, NotLoginView, AdminRequiredView
from app.app_ui_test.blueprint import app_ui_test
from app.app_ui_test.models.report import AppUiReport as Report, AppUiReportStep, AppUiReportCase, AppUiReport
from app.app_ui_test.forms.report import GetReportForm, FindReportForm, DeleteReportForm, GetReportCaseForm, \
    GetReportCaseListForm, GetReportStepForm, GetReportStepListForm, GetReportStepImgForm
from utils.util.fileUtil import FileUtil
from utils.view.required import login_required


class AppUiReportListView(LoginRequiredView):

    def post(self):
        """ 报告列表 """
        form = FindReportForm().do_validate()
        return app.restful.success(data=Report.make_pagination(form))


class AppReportIsDoneView(NotLoginView):
    def get(self):
        """ 根据运行id获取当次报告是否全部生成 """
        batch_id, process, status = request.args["batch_id"], request.args.get("process", 1), request.args.get("status",
                                                                                                               1)
        return app.restful.success(
            "获取成功",
            data=Report.select_is_all_status_by_batch_id(batch_id, [int(process), int(status)])
        )


class AppReportGetReportIdView(NotLoginView):
    def get(self):
        """ 根据运行id获取当次要打开的报告 """
        batch_id = request.args["batch_id"]
        return app.restful.success("获取成功", data=Report.select_show_report_id(batch_id))


class AppUiReportView(NotLoginView):

    def get(self):
        """ 获取测试报告 """
        form = GetReportForm().do_validate()
        return app.restful.success("获取成功", data=form.report.to_dict())

    @login_required
    def delete(self):
        """ 删除测试报告 """
        form = DeleteReportForm().do_validate()
        AppUiReport.batch_delete_report(form.report_id_list)
        FileUtil.delete_report_img_by_report_id(form.report_id_list, 'app')
        return app.restful.success("删除成功")


class AppUiReportClearView(LoginRequiredView):
    def delete(self):
        """ 清除测试报告 """
        AppUiReport.batch_delete_report_case(AppUiReportCase, AppUiReportStep)
        return app.restful.success("清除成功")


class AppUiGetReportCaseListView(NotLoginView):
    def get(self):
        """ 报告的用例列表 """
        form = GetReportCaseListForm().do_validate()
        case_list = AppUiReportCase.get_case_list(form.report_id.data, form.get_summary.data)
        return app.restful.success(data=case_list)


class AppUiGetReportCaseView(NotLoginView):
    def get(self):
        """ 报告的用例数据 """
        form = GetReportCaseForm().do_validate()
        return app.restful.success(data=form.case_data.to_dict())


class AppUiGetReportStepListView(NotLoginView):
    def get(self):
        """ 报告的步骤列表 """
        form = GetReportStepListForm().do_validate()
        step_list = AppUiReportStep.get_step_list(form.report_case_id.data, form.get_summary.data)
        return app.restful.success(data=step_list)


class AppUiGetReportStepView(NotLoginView):
    def get(self):
        """ 报告的步骤数据 """
        form = GetReportStepForm().do_validate()
        return app.restful.success(data=form.step_data.to_dict())


class AppUiGetReportStepImgView(NotLoginView):
    def post(self):
        """ 报告的步骤截图 """
        form = GetReportStepImgForm().do_validate()
        data = FileUtil.get_report_step_img(form.report_id.data, form.report_step_id.data, form.img_type.data, 'app')
        return app.restful.get_success({"data": data, "total": 1 if data else 0})


app_ui_test.add_url_rule("/report", view_func=AppUiReportView.as_view("AppUiReportView"))
app_ui_test.add_url_rule("/report/list", view_func=AppUiReportListView.as_view("AppUiReportListView"))
app_ui_test.add_url_rule("/report/clear", view_func=AppUiReportClearView.as_view("AppUiReportClearView"))
app_ui_test.add_url_rule("/report/status", view_func=AppReportIsDoneView.as_view("AppReportIsDoneView"))
app_ui_test.add_url_rule("/report/showId", view_func=AppReportGetReportIdView.as_view("AppReportGetReportIdView"))
app_ui_test.add_url_rule("/report/case", view_func=AppUiGetReportCaseView.as_view("AppUiGetReportCaseView"))
app_ui_test.add_url_rule("/report/case/list",
                         view_func=AppUiGetReportCaseListView.as_view("AppUiGetReportCaseListView"))
app_ui_test.add_url_rule("/report/step", view_func=AppUiGetReportStepView.as_view("AppUiGetReportStepView"))
app_ui_test.add_url_rule("/report/step/list",
                         view_func=AppUiGetReportStepListView.as_view("AppUiGetReportStepListView"))
app_ui_test.add_url_rule("/report/step/img",
                         view_func=AppUiGetReportStepImgView.as_view("AppUiGetReportStepImgView"))
