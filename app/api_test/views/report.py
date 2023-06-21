# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.baseView import LoginRequiredView, NotLoginView
from app.api_test.blueprint import api_test
from app.api_test.models.report import ApiReport as Report, ApiReportStep
from app.api_test.forms.report import GetReportForm, FindReportForm, DeleteReportForm, FindReportStepForm, \
    FindReportStepListForm
from utils.view.required import login_required


class ApiGetReportListView(LoginRequiredView):
    def post(self):
        """ 报告列表 """
        form = FindReportForm().do_validate()
        return app.restful.success(data=Report.make_pagination(form))


class ApiReportIsDoneView(NotLoginView):
    def get(self):
        """ 根据运行id获取当次报告是否全部生成 """
        batch_id, process, status = request.args["batch_id"], request.args.get("process", 1), request.args.get("status",
                                                                                                               1)
        return app.restful.success(
            "获取成功",
            data=Report.select_is_all_status_by_batch_id(batch_id, [int(process), int(status)])
        )


class ApiReportGetReportIdView(NotLoginView):
    def get(self):
        """ 根据运行id获取当次要打开的报告 """
        batch_id = request.args["batch_id"]
        return app.restful.success("获取成功", data=Report.select_show_report_id(batch_id))


class ApiReportView(LoginRequiredView):

    def get(self):
        """ 获取测试报告 """
        form = GetReportForm().do_validate()
        return app.restful.success("获取成功", data=form.report.to_dict())

    @login_required
    def delete(self):
        """ 删除测试报告 """
        form = DeleteReportForm().do_validate()
        for report in form.report_list:
            ApiReportStep.delete_by_report(report.id)
            report.delete()
        return app.restful.success("删除成功")


class ApiGetReportStepListView(LoginRequiredView):
    def get(self):
        """ 报告的步骤列表 """
        form = FindReportStepListForm().do_validate()
        # 性能考虑，只查关键字段
        fields = ["id", "name", "process", "result"]
        query_data = ApiReportStep.query.filter(ApiReportStep.report_id == form.report_id.data).with_entities(
            ApiReportStep.id, ApiReportStep.name, ApiReportStep.process, ApiReportStep.result
        ).all()  # [(24, '登录', 'before', 'running')]
        return app.restful.success(data=[dict(zip(fields, d)) for d in query_data])


class ApiGetReportStepView(NotLoginView):
    def get(self):
        """ 报告的步骤数据 """
        form = FindReportStepForm().do_validate()
        return app.restful.success(data=form.step_data.to_dict())


api_test.add_url_rule("/report", view_func=ApiReportView.as_view("ApiReportView"))
api_test.add_url_rule("/report/list", view_func=ApiGetReportListView.as_view("ApiGetReportListView"))
api_test.add_url_rule("/report/status", view_func=ApiReportIsDoneView.as_view("ApiReportIsDoneView"))
api_test.add_url_rule("/report/showId", view_func=ApiReportGetReportIdView.as_view("ApiReportGetReportIdView"))
api_test.add_url_rule("/report/step", view_func=ApiGetReportStepView.as_view("ApiGetReportStepView"))
api_test.add_url_rule("/report/step/list", view_func=ApiGetReportStepListView.as_view("ApiGetReportStepListView"))
