# -*- coding: utf-8 -*-

from flask import request, current_app as app

from app.baseView import LoginRequiredView
from app.web_ui_test import web_ui_test
from app.baseModel import db
from config.config import (ui_action_mapping_list, ui_assert_mapping_list, ui_extract_mapping_list)
from app.web_ui_test.models.step import UiStep
from app.web_ui_test.forms.step import GetStepListForm, GetStepForm, AddStepForm, EditStepForm

ns = web_ui_test.namespace("step", description="测试步骤管理相关接口")


@ns.route('/list/')
class WebUiGetStepListView(LoginRequiredView):

    def get(self):
        """ 根据用例id获取步骤列表 """
        form = GetStepListForm()
        if form.validate():
            step_obj_list = UiStep.query.filter_by(case_id=form.caseId.data).order_by(UiStep.num.asc()).all()
            return app.restful.success('获取成功', data=[step.to_dict() for step in step_obj_list])
        return app.restful.error(form.get_error())


@ns.route('/execute/')
class WebUiGetCaseExecuteListView(LoginRequiredView):

    def get(self):
        """ 获取执行动作类型列表 """
        return app.restful.success('获取成功', data=ui_action_mapping_list)


@ns.route('/extractMapping/')
class WebUiGetExtractMappingListView(LoginRequiredView):

    def get(self):
        """ 数据提取方法列表 """
        return app.restful.success('获取成功', data=ui_extract_mapping_list)


@ns.route('/assertMapping/')
class WebUiGetAssertMappingListView(LoginRequiredView):

    def get(self):
        """ 断言方法列表 """
        return app.restful.success('获取成功', data=ui_assert_mapping_list)


@ns.route('/changeIsRun/')
class WebUiChangeStepStatusView(LoginRequiredView):

    def put(self):
        """ 修改步骤状态（是否执行） """
        with db.auto_commit():
            UiStep.get_first(id=request.json.get('id')).is_run = request.json.get('is_run')
        return app.restful.success(f'步骤已修改为 {"执行" if request.json.get("is_run") else "不执行"}')


@ns.route('/sort/')
class WebUiChangeStepSortView(LoginRequiredView):

    def put(self):
        """ 更新步骤的排序 """
        UiStep.change_sort(request.json.get('List'), request.json.get('pageNum', 0), request.json.get('pageSize', 0))
        return app.restful.success(msg='修改排序成功')


@ns.route('/copy/')
class WebUiCopyStepView(LoginRequiredView):

    def post(self):
        """ 复制步骤 """
        old = UiStep.get_first(id=request.json.get('id')).to_dict()
        old['name'] = f"{old['name']}_copy"
        old['num'] = UiStep.get_insert_num(case_id=old['case_id'])
        step = UiStep().create(old)
        return app.restful.success(msg='步骤复制成功', data=step.to_dict())


@ns.route('/')
class WebUiStepMethodViewView(LoginRequiredView):

    def get(self):
        """ 获取步骤 """
        form = GetStepForm()
        if form.validate():
            return app.restful.success('获取成功', data=form.step.to_dict())
        return app.restful.error(form.get_error())

    def post(self):
        """ 新增步骤 """
        form = AddStepForm()
        if form.validate():
            form.num.data = UiStep.get_insert_num(case_id=form.case_id.data)
            step = UiStep().create(form.data)
            return app.restful.success(f'步骤【{step.name}】新建成功', data=step.to_dict())
        return app.restful.error(form.get_error())

    def put(self):
        """ 修改步骤 """
        form = EditStepForm()
        if form.validate():
            form.step.update(form.data)
            return app.restful.success(msg=f'步骤【{form.step.name}】修改成功', data=form.step.to_dict())
        return app.restful.fail(form.get_error())

    def delete(self):
        """ 删除步骤 """
        form = GetStepForm()
        if form.validate():
            form.step.delete()
            return app.restful.success(f'步骤【{form.step.name}】删除成功')
        return app.restful.error(form.get_error())
