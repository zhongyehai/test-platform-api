# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.api_test import api_test
from app.baseModel import db
from app.api_test.models.step import ApiStep as Step
from app.api_test.forms.step import GetStepListForm, GetStepForm, AddStepForm, EditStepForm
from app.baseView import LoginRequiredView

ns = api_test.namespace("step", description="测试步骤管理相关接口")


@ns.route('/list/')
class ApiGetStepListView(LoginRequiredView):
    def get(self):
        """ 根据用例id获取步骤列表 """
        form = GetStepListForm()
        if form.validate():
            step_obj_list = Step.query.filter_by(case_id=form.caseId.data).order_by(Step.num.asc()).all()
            return app.restful.success('获取成功', data=[step.to_dict() for step in step_obj_list])
        return app.restful.error(form.get_error())


@ns.route('/changeIsRun/')
class ApiChangeStepStatusView(LoginRequiredView):
    def put(self):
        """ 修改步骤状态（是否执行） """
        with db.auto_commit():
            Step.get_first(id=request.json.get('id')).is_run = request.json.get('is_run')
        return app.restful.success(f'步骤已修改为 {"执行" if request.json.get("is_run") else "不执行"}')


@ns.route('/changeHost/')
class ApiChangeStepHostView(LoginRequiredView):
    def put(self):
        """ 修改步骤引用的host """
        step = Step.get_first(id=request.json.get('id'))
        with db.auto_commit():
            step.replace_host = request.json.get('replace_host')
        return app.restful.success(
            f'步骤已修改为 {"使用【用例】所在服务的host" if request.json.get("replace_host") else "使用【接口】所在服务的host"}',
            data=step.to_dict()
        )


@ns.route('/sort/')
class ApiChangeStepSortView(LoginRequiredView):
    def put(self):
        """ 更新步骤的排序 """
        Step.change_sort(request.json.get('List'), request.json.get('pageNum', 0), request.json.get('pageSize', 0))
        return app.restful.success(msg='修改排序成功')


@ns.route('/copy/')
class ApiCopyStepView(LoginRequiredView):

    def post(self):
        """ 复制步骤 """
        old = Step.get_first(id=request.json.get('id')).to_dict()
        old['name'] = f"{old['name']}_copy"
        old['num'] = Step.get_insert_num(case_id=old['case_id'])
        step = Step().create(old)
        step.add_api_quote_count()
        return app.restful.success(msg='步骤复制成功', data=step.to_dict())


@ns.route('/')
class ApiStepMethodView(LoginRequiredView):

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
            form.num.data = Step.get_insert_num(case_id=form.case_id.data)
            step = Step().create(form.data)
            step.add_api_quote_count()
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
            form.step.subtract_api_quote_count()
            return app.restful.success(f'步骤【{form.step.name}】删除成功')
        return app.restful.error(form.get_error())
