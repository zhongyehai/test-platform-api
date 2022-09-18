# -*- coding: utf-8 -*-

import json
from threading import Thread

from flask import request, g, current_app as app

from app.baseView import LoginRequiredView
from app.web_ui_test import web_ui_test
from utils.client.runUiTest.runUiTestRunner import RunCase
from app.baseModel import db
from app.web_ui_test.models.case import WebUiCase as Case
from app.web_ui_test.models.step import WebUiStep as Step
from app.web_ui_test.models.report import WebUiReport as Report
from app.web_ui_test.models.caseSet import WebUiCaseSet as CaseSet
from app.web_ui_test.forms.case import AddCaseForm, EditCaseForm, FindCaseForm, DeleteCaseForm, GetCaseForm, \
    RunCaseForm, CopyCaseStepForm

ns = web_ui_test.namespace("case", description="用例管理相关接口")


@ns.route('/list/')
class WebUiGetCaseListView(LoginRequiredView):

    def get(self):
        """ 根据用例集查找用例列表 """
        form = FindCaseForm()
        if form.validate():
            return app.restful.success(data=Case.make_pagination(form))
        return app.restful.fail(form.get_error())


@ns.route('/name/')
class WebUiGetCaseNameView(LoginRequiredView):

    def get(self):
        """ 根据用例id获取用例名 """
        # caseId: '1,4,12'
        case_ids: list = request.args.to_dict().get('caseId').split(',')
        return app.restful.success(
            data=[{'id': int(case_id), 'name': Case.get_first(id=case_id).name} for case_id in case_ids])


@ns.route('/quote/')
class WebUiChangeCaseQuoteView(LoginRequiredView):

    def put(self):
        """ 更新用例引用 """
        case_id, quote_type, quote = request.json.get('id'), request.json.get('quoteType'), request.json.get('quote')
        with db.auto_commit():
            case = Case.get_first(id=case_id)
            setattr(case, quote_type, json.dumps(quote))
        return app.restful.success(msg='引用关系修改成功')


@ns.route('/sort/')
class WebUiChangeCaseSortView(LoginRequiredView):

    def put(self):
        """ 更新用例的排序 """
        Case.change_sort(request.json.get('List'), request.json.get('pageNum'), request.json.get('pageSize'))
        return app.restful.success(msg='修改排序成功')


@ns.route('/run/')
class WebUiRunCaseView(LoginRequiredView):

    def post(self):
        """ 运行测试用例 """
        form = RunCaseForm()
        if form.validate():
            case = form.case
            project_id = CaseSet.get_first(id=case.set_id).project_id
            report = Report.get_new_report(case.name, 'case', g.user_name, g.user_id, project_id)

            # 新起线程运行用例
            Thread(
                target=RunCase(
                    project_id=project_id,
                    run_name=report.name,
                    case_id=form.caseId.data,
                    report_id=report.id,
                    env=form.env.data
                ).run_case
            ).start()
            return app.restful.success(msg='触发执行成功，请等待执行完毕', data={'report_id': report.id})
        return app.restful.fail(form.get_error())


@ns.route('/changeIsRun/')
class WebUiChangeCaseStatusView(LoginRequiredView):

    def put(self):
        """ 修改用例状态（是否执行） """
        with db.auto_commit():
            Case.get_first(id=request.json.get('id')).is_run = request.json.get('is_run')
        return app.restful.success(f'用例已修改为 {"执行" if request.json.get("is_run") else "不执行"}')


@ns.route('/copy/')
class WebUiCopyCaseView(LoginRequiredView):

    def post(self):
        """ 复制用例 """
        case_id = request.json.get('id')
        case = Case.get_first(id=case_id)
        with db.auto_commit():
            old_case = case.to_dict()
            old_case['create_user'] = old_case['update_user'] = g.user_id
            new_case = Case()
            new_case.create(old_case)
            new_case.name = old_case['name'] + '_copy'
            new_case.num = Case.get_insert_num(set_id=old_case['set_id'])
            db.session.add(new_case)

        # 复制步骤
        old_step_list = Step.query.filter_by(case_id=case_id).order_by(Step.num.asc()).all()
        for index, old_step in enumerate(old_step_list):
            step = old_step.to_dict()
            step['num'], step['case_id'] = index, new_case.id
            new_step = Step().create(step)
            new_step.add_api_quote_count()

        return app.restful.success(
            '复制成功',
            data={
                'case': new_case.to_dict(),
                'steps': [step.to_dict() for step in Step.get_all(case_id=new_case.id)]
            }
        )


@ns.route('/copy/step/')
class WebUiCopyCaseStepView(LoginRequiredView):

    def post(self):
        """ 复制指定用例的步骤到当前用例下 """
        form = CopyCaseStepForm()
        if form.validate():
            from_case, to_case = form.source_case, form.to_case
            step_list, num_start = [], Step.get_max_num(case_id=to_case.id)
            for index, step in enumerate(Step.get_all(case_id=from_case.id)):
                step_dict = step.to_dict()
                step_dict['case_id'], step_dict['num'] = to_case.id, num_start + index + 1
                step_list.append(Step().create(step_dict).to_dict())
            return app.restful.success('步骤复制成功', data=step_list)
        return app.restful.fail(form.get_error())


@ns.route('/')
class WebUiCaseViewView(LoginRequiredView):

    def get(self):
        """ 获取用例 """
        form = GetCaseForm()
        if form.validate():
            return app.restful.success('获取成功', data=form.case.to_dict())
        return app.restful.fail(form.get_error())

    def post(self):
        """ 新增用例 """
        form = AddCaseForm()
        if form.validate():
            form.num.data = Case.get_insert_num(set_id=form.set_id.data)
            new_case = Case().create(form.data)
            return app.restful.success(f'用例【{new_case.name}】新建成功', data=new_case.to_dict())
        return app.restful.fail(form.get_error())

    def put(self):
        """ 修改用例 """
        form = EditCaseForm()
        if form.validate():
            form.old_data.update(form.data)
            return app.restful.success(msg=f'用例【{form.old_data.name}】修改成功', data=form.old_data.to_dict())
        return app.restful.fail(form.get_error())

    def delete(self):
        """ 删除用例 """
        form = DeleteCaseForm()
        if form.validate():
            form.case.delete_current_and_step()
            return app.restful.success(f'用例【{form.case.name}】删除成功')
        return app.restful.fail(form.get_error())
