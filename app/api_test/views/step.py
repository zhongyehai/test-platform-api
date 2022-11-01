# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.api_test.blueprint import api_test
from app.api_test.models.step import ApiStep as Step
from app.api_test.models.case import ApiCase as Case
from app.api_test.forms.step import GetStepListForm, GetStepForm, AddStepForm, EditStepForm
from app.baseView import LoginRequiredView
from app.busines import StepBusiness


class ApiGetStepListView(LoginRequiredView):
    def get(self):
        """ 根据用例id获取步骤列表 """
        form = GetStepListForm().do_validate()
        step_obj_list = Step.query.filter_by(case_id=form.caseId.data).order_by(Step.num.asc()).all()
        return app.restful.success('获取成功', data=[step.to_dict() for step in step_obj_list])


class ApiChangeStepStatusView(LoginRequiredView):
    def put(self):
        """ 修改步骤状态（是否执行） """
        Step.get_first(id=request.json.get('id')).update(request.json)
        return app.restful.success("运行状态修改成功")


class ApiChangeStepHostView(LoginRequiredView):
    def put(self):
        """ 修改步骤引用的host """
        step = Step.get_first(id=request.json.get('id'))
        step.update(request.json)
        return app.restful.success(
            f'步骤已修改为 {"使用【用例】所在服务的host" if request.json.get("replace_host") else "使用【接口】所在服务的host"}',
            data=step.to_dict()
        )


class ApiChangeStepSortView(LoginRequiredView):
    def put(self):
        """ 更新步骤的排序 """
        Step.change_sort(request.json.get('List'), request.json.get('pageNum', 0), request.json.get('pageSize', 0))
        return app.restful.success(msg='修改排序成功')


class ApiCopyStepView(LoginRequiredView):

    def post(self):
        """ 复制步骤 """
        step = StepBusiness.copy(request.json.get('id'), Step, step_type='api')
        return app.restful.success(msg='步骤复制成功', data=step.to_dict())


class ApiStepMethodView(LoginRequiredView):

    def get(self):
        """ 获取步骤 """
        form = GetStepForm().do_validate()
        return app.restful.success('获取成功', data=form.step.to_dict())

    def post(self):
        """ 新增步骤 """
        form = AddStepForm().do_validate()
        step = StepBusiness.post(form, Step, Case, step_type='api')
        return app.restful.success(
            f'步骤【{step.name}】新建成功{", 自定义变量已合并至当前用例" if step.quote_case else ""}',
            data=step.to_dict()
        )

    def put(self):
        """ 修改步骤 """
        form = EditStepForm().do_validate()
        form.step.update(form.data)
        return app.restful.success(msg=f'步骤【{form.step.name}】修改成功', data=form.step.to_dict())

    def delete(self):
        """ 删除步骤 """
        form = GetStepForm().do_validate()
        form.step.delete()
        form.step.subtract_api_quote_count()
        return app.restful.success(f'步骤【{form.step.name}】删除成功')


api_test.add_url_rule('/step', view_func=ApiStepMethodView.as_view('ApiStepMethodView'))
api_test.add_url_rule('/step/copy', view_func=ApiCopyStepView.as_view('ApiCopyStepView'))
api_test.add_url_rule('/step/list', view_func=ApiGetStepListView.as_view('ApiGetStepListView'))
api_test.add_url_rule('/step/sort', view_func=ApiChangeStepSortView.as_view('ApiChangeStepSortView'))
api_test.add_url_rule('/step/changeHost', view_func=ApiChangeStepHostView.as_view('ApiChangeStepHostView'))
api_test.add_url_rule('/step/changeIsRun', view_func=ApiChangeStepStatusView.as_view('ApiChangeStepStatusView'))
