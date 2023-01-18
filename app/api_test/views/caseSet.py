# -*- coding: utf-8 -*-
from flask import current_app as app, request, g

from app.api_test.models.case import ApiCase as Case
from app.api_test.models.report import ApiReport as Report
from app.baseView import LoginRequiredView
from app.busines import RunCaseBusiness
from utils.client.runApiTest import RunCase
from app.api_test.blueprint import api_test
from app.api_test.models.caseSet import ApiCaseSet as CaseSet
from app.api_test.forms.caseSet import AddCaseSetForm, EditCaseSetForm, FindCaseSet, GetCaseSetEditForm, \
    DeleteCaseSetForm, RunCaseSetForm


class ApiGetCaseSetListView(LoginRequiredView):

    def get(self):
        """ 获取用例集列表 """
        form = FindCaseSet().do_validate()
        return app.restful.success(data=CaseSet.make_pagination(form))


class ApiCaseSetRunView(LoginRequiredView):

    def post(self):
        """ 运行用例集下的用例 """
        form = RunCaseSetForm().do_validate()
        report_id = RunCaseBusiness.run(
            env_code=form.env_code.data,
            is_async=form.is_async.data,
            project_id=form.set.project_id,
            report_name=form.set.name,
            task_type="set",
            report_model=Report,
            case_id=form.set.get_run_case_id(Case, form.business_id.data),
            run_type="api",
            run_func=RunCase
        )
        return app.restful.success(msg="触发执行成功，请等待执行完毕", data={"report_id": report_id})


class ApiCaseSetTreeView(LoginRequiredView):

    def get(self):
        """ 获取指定服务下的用例集列表 """
        set_list = [
            case_set.to_dict() for case_set in CaseSet.query.filter_by(
                project_id=int(request.args.get("project_id"))).order_by(CaseSet.parent.asc()).all()
        ]
        return app.restful.success(data=set_list)


class ApiCaseSetView(LoginRequiredView):
    """ 用例集管理 """

    def get(self):
        """ 获取用例集 """
        form = GetCaseSetEditForm().do_validate()
        return app.restful.success(data={"name": form.set.name, "num": form.set.num})

    def post(self):
        """ 新增用例集 """
        form = AddCaseSetForm().do_validate()
        form.num.data = CaseSet.get_insert_num(project_id=form.project_id.data)
        new_set = CaseSet().create(form.data)
        return app.restful.success(f"用例集【{form.name.data}】创建成功", new_set.to_dict())

    def put(self):
        """ 修改用例集 """
        form = EditCaseSetForm().do_validate()
        form.case_set.update(form.data)
        return app.restful.success(f"用例集【{form.name.data}】修改成功", form.case_set.to_dict())

    def delete(self):
        """ 删除用例集 """
        form = DeleteCaseSetForm().do_validate()
        form.case_set.delete()
        return app.restful.success("删除成功")


api_test.add_url_rule("/caseSet", view_func=ApiCaseSetView.as_view("ApiCaseSetView"))
api_test.add_url_rule("/caseSet/run", view_func=ApiCaseSetRunView.as_view("ApiCaseSetRunView"))
api_test.add_url_rule("/caseSet/tree", view_func=ApiCaseSetTreeView.as_view("ApiCaseSetTreeView"))
api_test.add_url_rule("/caseSet/list", view_func=ApiGetCaseSetListView.as_view("ApiGetCaseSetListView"))
