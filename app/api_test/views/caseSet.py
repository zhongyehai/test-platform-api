# -*- coding: utf-8 -*-
from threading import Thread

from flask import current_app as app, request, g

from app.api_test.models.case import ApiCase as Case
from app.api_test.models.report import ApiReport as Report
from app.baseView import LoginRequiredView
from utils.client.runApiTest.runHttpRunner import RunCase
from app.api_test import api_test
from app.api_test.models.caseSet import ApiCaseSet as CaseSet
from app.api_test.forms.caseSet import AddCaseSetForm, EditCaseSetForm, FindCaseSet, GetCaseSetEditForm, \
    DeleteCaseSetForm, RunCaseSetForm

ns = api_test.namespace("caseSet", description="用例集管理相关接口")


@ns.route('/list/')
class ApiGetCaseSetListView(LoginRequiredView):

    def get(self):
        """ 获取用例集列表 """
        form = FindCaseSet()
        if form.validate():
            return app.restful.success(data=CaseSet.make_pagination(form))
        return app.restful.fail(form.get_error())


@ns.route('/run/')
class ApiCaseSetRunView(LoginRequiredView):

    def post(self):
        """ 运行用例集下的用例 """
        form = RunCaseSetForm()
        if form.validate():
            project_id = form.set.project_id
            report = Report.get_new_report(form.set.name, 'set', g.user_name, g.user_id, project_id)

            # 新起线程运行任务
            Thread(
                target=RunCase(
                    project_id=project_id,
                    run_name=report.name,
                    case_id=[case.id for case in Case.query.filter_by(set_id=form.set.id).order_by(Case.num.asc()).all()
                             if case.is_run],
                    report_id=report.id,
                    is_async=form.is_async.data,
                    env=form.env.data
                ).run_case
            ).start()
            return app.restful.success(msg='触发执行成功，请等待执行完毕', data={'report_id': report.id})
        return app.restful.fail(form.get_error())


@ns.route('/tree/')
class ApiCaseSetTreeView(LoginRequiredView):

    def get(self):
        """ 获取指定服务下的用例集列表 """
        set_list = [
            case_set.to_dict() for case_set in CaseSet.query.filter_by(
                project_id=int(request.args.get('project_id'))).order_by(CaseSet.parent.asc()).all()
        ]
        return app.restful.success(data=set_list)


@ns.route('/')
class ApiCaseSetView(LoginRequiredView):
    """ 用例集管理 """

    def get(self):
        """ 获取用例集 """
        form = GetCaseSetEditForm()
        if form.validate():
            return app.restful.success(data={'name': form.set.name, 'num': form.set.num})
        return app.restful.fail(form.get_error())

    def post(self):
        """ 新增用例集 """
        form = AddCaseSetForm()
        if form.validate():
            form.num.data = CaseSet.get_insert_num(project_id=form.project_id.data)
            new_set = CaseSet().create(form.data)
            return app.restful.success(f'用例集【{form.name.data}】创建成功', new_set.to_dict())
        return app.restful.fail(form.get_error())

    def put(self):
        """ 修改用例集 """
        form = EditCaseSetForm()
        if form.validate():
            form.case_set.update(form.data)
            return app.restful.success(f'用例集【{form.name.data}】修改成功', form.case_set.to_dict())
        return app.restful.fail(form.get_error())

    def delete(self):
        """ 删除用例集 """
        form = DeleteCaseSetForm()
        if form.validate():
            form.case_set.delete()
            return app.restful.success('删除成功')
        return app.restful.fail(form.get_error())
