# -*- coding: utf-8 -*-
from selenium.webdriver.common.keys import Keys
from flask import request, current_app as app

from app.baseView import LoginRequiredView
from app.busines import StepBusiness
from app.web_ui_test.blueprint import web_ui_test
from config import ui_action_mapping_list, ui_assert_mapping_list, ui_extract_mapping_list
from app.web_ui_test.models.step import WebUiStep as Step
from app.web_ui_test.models.case import WebUiCase as Case
from app.web_ui_test.forms.step import GetStepListForm, GetStepForm, AddStepForm, EditStepForm, ChangeStepStatusForm, \
    DeleteStepForm


class WebUiGetStepListView(LoginRequiredView):

    def get(self):
        """ 根据用例id获取步骤列表 """
        form = GetStepListForm().do_validate()
        step_obj_list = Step.query.filter_by(case_id=form.caseId.data).order_by(Step.num.asc()).all()
        return app.restful.success("获取成功", data=[step.to_dict() for step in step_obj_list])


class WebUiGetCaseExecuteListView(LoginRequiredView):

    def get(self):
        """ 获取执行动作类型列表 """
        return app.restful.success("获取成功", data=ui_action_mapping_list)


class WebUiGetKeyBoardCodeListView(LoginRequiredView):

    def get(self):
        """ 获取键盘映射 """
        data = {key: f'按键【{key}】' for key in dir(Keys) if key.startswith('_') is False}
        return app.restful.success("获取成功", data=data)


class WebUiGetExtractMappingListView(LoginRequiredView):

    def get(self):
        """ 数据提取方法列表 """
        return app.restful.success("获取成功", data=ui_extract_mapping_list)


class WebUiGetAssertMappingListView(LoginRequiredView):

    def get(self):
        """ 断言方法列表 """
        return app.restful.success("获取成功", data=ui_assert_mapping_list)


class WebUiChangeStepStatusView(LoginRequiredView):

    def put(self):
        """ 修改步骤状态（是否执行） """
        form = ChangeStepStatusForm().do_validate()
        for step in form.step_list:
            step.change_status(form.status.data)
        return app.restful.success("运行状态修改成功")


class WebUiChangeStepSortView(LoginRequiredView):

    def put(self):
        """ 更新步骤的排序 """
        Step.change_sort(request.json.get("List"), request.json.get("pageNum", 0), request.json.get("pageSize", 0))
        return app.restful.success(msg="修改排序成功")


class WebUiCopyStepView(LoginRequiredView):

    def post(self):
        """ 复制步骤 """
        step_id, case_id = request.json.get("id"), request.json.get("caseId")
        step = StepBusiness.copy(step_id, case_id, Step)
        return app.restful.success(msg="步骤复制成功", data=step.to_dict())


class WebUiStepMethodViewView(LoginRequiredView):

    def get(self):
        """ 获取步骤 """
        form = GetStepForm().do_validate()
        return app.restful.success("获取成功", data=form.step.to_dict())

    def post(self):
        """ 新增步骤 """
        form = AddStepForm().do_validate()
        step = StepBusiness.post(form, Step, Case)
        return app.restful.success(
            f'步骤【{step.name}】新建成功{", 自定义变量已合并至当前用例，请处理" if step.quote_case else ""}',
            data=step.to_dict()
        )

    def put(self):
        """ 修改步骤 """
        form = EditStepForm().do_validate()
        form.step.update(form.data)
        return app.restful.success(msg=f"步骤【{form.step.name}】修改成功", data=form.step.to_dict())

    def delete(self):
        """ 删除步骤 """
        form = DeleteStepForm().do_validate()
        for step in form.step_list:
            step.delete()
            step.subtract_api_quote_count()
        return app.restful.success(f"步骤删除成功")


web_ui_test.add_url_rule("/step/copy", view_func=WebUiCopyStepView.as_view("WebUiCopyStepView"))
web_ui_test.add_url_rule("/step/list", view_func=WebUiGetStepListView.as_view("WebUiGetStepListView"))
web_ui_test.add_url_rule("/step", view_func=WebUiStepMethodViewView.as_view("WebUiStepMethodViewView"))
web_ui_test.add_url_rule("/step/sort", view_func=WebUiChangeStepSortView.as_view("WebUiChangeStepSortView"))
web_ui_test.add_url_rule("/step/status", view_func=WebUiChangeStepStatusView.as_view("WebUiChangeStepStatusView"))
web_ui_test.add_url_rule("/step/execute", view_func=WebUiGetCaseExecuteListView.as_view("WebUiGetCaseExecuteListView"))
web_ui_test.add_url_rule("/step/keyBoardCode",
                         view_func=WebUiGetKeyBoardCodeListView.as_view("WebUiGetKeyBoardCodeListView"))
web_ui_test.add_url_rule("/step/assertMapping",
                         view_func=WebUiGetAssertMappingListView.as_view("WebUiGetAssertMappingListView"))
web_ui_test.add_url_rule("/step/extractMapping",
                         view_func=WebUiGetExtractMappingListView.as_view("WebUiGetExtractMappingListView"))
