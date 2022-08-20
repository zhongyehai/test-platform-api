# -*- coding: utf-8 -*-
import json
from threading import Thread

from flask import current_app as app, request, g, views

from app.api_test import api_test
from utils.client.runApiTest.runHttpRunner import RunCase
from app.baseModel import db
from app.api_test.models.case import ApiCase
from app.api_test.models.step import ApiStep as Step
from app.api_test.models.report import ApiReport as Report
from app.api_test.models.caseSet import ApiSet
from app.api_test.forms.case import AddCaseForm, EditCaseForm, FindCaseForm, DeleteCaseForm, GetCaseForm, RunCaseForm


def create_step(index, case_id, old_step):
    """ 插入步骤 """
    old_step["num"] = index
    old_step["case_id"] = case_id
    return Step().create(old_step)


@api_test.route('/case/list', methods=['get'])
def api_get_case_list():
    """ 根据模块查找用例list """
    form = FindCaseForm()
    if form.validate():
        return app.restful.success(data=ApiCase.make_pagination(form))
    return app.restful.fail(form.get_error())


@api_test.route('/case/name', methods=['get'])
def api_get_case_name():
    """ 根据用例id获取用例名 """
    # caseId: '1,4,12'
    case_ids: list = request.args.to_dict().get('caseId').split(',')
    return app.restful.success(
        data=[{'id': int(case_id), 'name': ApiCase.get_first(id=case_id).name} for case_id in case_ids])


@api_test.route('/case/quote', methods=['put'])
def api_change_case_quote():
    """ 更新用例引用 """
    case_id, quote_type, quote = request.json.get('id'), request.json.get('quoteType'), request.json.get('quote')
    with db.auto_commit():
        case = ApiCase.get_first(id=case_id)
        setattr(case, quote_type, json.dumps(quote))
    return app.restful.success(msg='引用关系修改成功')


@api_test.route('/case/sort', methods=['put'])
def api_change_case_sort():
    """ 更新用例的排序 """
    ApiCase.change_sort(request.json.get('List'), request.json.get('pageNum'), request.json.get('pageSize'))
    return app.restful.success(msg='修改排序成功')


@api_test.route('/case/run', methods=['POST'])
def api_run_case():
    """ 运行测试用例，并生成报告 """
    form = RunCaseForm()
    if form.validate():
        case, case_list = form.case_list[0], form.case_list
        project_id = ApiSet.get_first(id=case.set_id).project_id

        report = Report.get_new_report(case.name, 'case', g.user_name, g.user_id, project_id)

        # 新起线程运行用例
        Thread(
            target=RunCase(
                project_id=project_id,
                run_name=report.name,
                case_id=form.caseId.data,
                report_id=report.id,
                is_async=False,
                env=form.env.data
            ).run_case
        ).start()
        return app.restful.success(msg='触发执行成功，请等待执行完毕', data={'report_id': report.id})
    return app.restful.fail(form.get_error())


@api_test.route('/case/changeIsRun', methods=['PUT'])
def api_change_case_status():
    """ 修改用例状态（是否执行） """
    with db.auto_commit():
        ApiCase.get_first(id=request.json.get('id')).is_run = request.json.get('is_run')
    return app.restful.success(f'用例已修改为 {"执行" if request.json.get("is_run") else "不执行"}')


@api_test.route('/case/copy', methods=['GET'])
def api_copy_case():
    """ 复制用例，返回复制的用例和步骤 """
    # 复制用例
    case = ApiCase.get_first(id=request.args.get('id'))
    with db.auto_commit():
        old_case = case.to_dict()
        old_case['create_user'] = old_case['update_user'] = g.user_id
        new_case = ApiCase()
        new_case.create(old_case, 'func_files', 'variables', 'headers')
        new_case.name = old_case['name'] + '_copy'
        new_case.num = ApiCase.get_insert_num(set_id=old_case['set_id'])
        db.session.add(new_case)

    # 复制步骤
    old_step_list = Step.query.filter_by(case_id=request.args.get('id')).order_by(Step.num.asc()).all()
    with db.auto_commit():
        for old_step in old_step_list:
            db.session.add(create_step(old_step.num, new_case.id, old_step.to_dict()))

    return app.restful.success(
        '复制成功',
        data={
            'case': new_case.to_dict(),
            'steps': [step.to_dict() for step in Step.get_all(case_id=new_case.id)]
        }
    )


class ApiCaseView(views.MethodView):
    """ 用例管理 """

    def get(self):
        form = GetCaseForm()
        if form.validate():
            return app.restful.success('获取成功', data=form.case.to_dict())
        return app.restful.fail(form.get_error())

    def post(self):
        form = AddCaseForm()
        if form.validate():
            form.num.data = ApiCase.get_insert_num(set_id=form.set_id.data)
            new_case = ApiCase().create(form.data)
            return app.restful.success(f'用例【{new_case.name}】新建成功', data=new_case.to_dict())
        return app.restful.fail(form.get_error())

    def put(self):
        form = EditCaseForm()
        if form.validate():
            form.case.update(form.data)
            return app.restful.success(msg=f'用例【{form.case.name}】修改成功', data=form.case.to_dict())
        return app.restful.fail(form.get_error())

    def delete(self):
        form = DeleteCaseForm()
        if form.validate():
            form.case.delete_current_and_step()
            return app.restful.success(f'用例【{form.case.name}】删除成功')
        return app.restful.fail(form.get_error())


api_test.add_url_rule('/case', view_func=ApiCaseView.as_view('api_case'))
