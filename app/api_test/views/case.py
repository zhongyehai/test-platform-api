# -*- coding: utf-8 -*-
import json

from flask import current_app as app, request

from app.api_test.blueprint import api_test
from app.baseView import LoginRequiredView
from app.busines import RunCaseBusiness, CaseBusiness
from utils.client.runApiTest import RunCase
from app.api_test.models.project import ApiProject as Project
from app.api_test.models.case import ApiCase as Case
from app.api_test.models.step import ApiStep as Step
from app.api_test.models.report import ApiReport as Report
from app.api_test.models.caseSet import ApiCaseSet as CaseSet
from app.api_test.forms.case import AddCaseForm, EditCaseForm, FindCaseForm, DeleteCaseForm, GetCaseForm, RunCaseForm, \
    CopyCaseStepForm, PullCaseStepForm


class ApiGetCaseListView(LoginRequiredView):

    def get(self):
        """ 根据模块获取用例list """
        form = FindCaseForm().do_validate()
        return app.restful.success(data=Case.make_pagination(form))


class ApiGetCaseNameByIdView(LoginRequiredView):

    def get(self):
        """ 根据用例id获取用例名 """
        # caseId: "1,4,12"
        case_ids: list = request.args.to_dict().get("caseId").split(",")
        return app.restful.success(
            data=[{"id": int(case_id), "name": Case.get_first(id=case_id).name} for case_id in case_ids])


class ApiChangeCaseQuoteView(LoginRequiredView):

    def put(self):
        """ 更新用例引用 """
        case_id, quote_type, quote = request.json.get("id"), request.json.get("quoteType"), request.json.get("quote")
        Case.get_first(id=case_id).update({quote_type: json.dumps(quote)})
        return app.restful.success(msg="引用关系修改成功")


class ApiChangeCaseSortView(LoginRequiredView):

    def put(self):
        """ 更新用例的排序 """
        Case.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class ApiRunCaseView(LoginRequiredView):

    def post(self):
        """ 运行测试用例，并生成报告 """
        form = RunCaseForm().do_validate()
        case = form.case_list[0]
        project_id = CaseSet.get_first(id=case.set_id).project_id
        report_id = RunCaseBusiness.run(
            env_code=form.env_code.data,
            is_async=form.is_async.data,
            project_id=project_id,
            report_name=case.name,
            task_type="case",
            report_model=Report,
            case_id=form.caseId.data,
            run_type="api",
            run_func=RunCase
        )
        return app.restful.success(msg="触发执行成功，请等待执行完毕", data={"report_id": report_id})


class ApiChangeCaseStatusView(LoginRequiredView):

    def put(self):
        """ 修改用例状态（是否执行） """
        Case.get_first(id=request.json.get("id")).change_status()
        return app.restful.success("运行状态修改成功")


class ApiCopyCaseView(LoginRequiredView):

    def post(self):
        """ 复制用例 """
        form = GetCaseForm().do_validate()
        data = CaseBusiness.copy(form, Case, Step, "api")
        return app.restful.success("复制成功", data=data)


class ApiCopyCaseStepView(LoginRequiredView):

    def post(self):
        """ 复制指定用例的步骤到当前用例下 """
        form = CopyCaseStepForm().do_validate()
        step_list = CaseBusiness.copy_step_to_current_case(form, Step)
        return app.restful.success("步骤复制成功", data=step_list)


class ApiGetQuoteCaseFromView(LoginRequiredView):

    def get(self):
        """ 获取用例的归属 """
        form = GetCaseForm().do_validate()
        from_path = CaseBusiness.get_quote_case_from(form.id.data, Project, CaseSet, Case)
        return app.restful.success("获取成功", data=from_path)


class ApiPullCaseStepView(LoginRequiredView):

    def post(self):
        """ 复制指定用例的步骤到当前用例下 """
        form = PullCaseStepForm().do_validate()
        CaseBusiness.pull_step_to_current_case(form, Step)
        return app.restful.success("步骤复制成功")


class ApiCaseView(LoginRequiredView):

    def get(self):
        """ 获取用例 """
        form = GetCaseForm().do_validate()
        return app.restful.success("获取成功", data=form.case.to_dict())

    def post(self):
        """ 新增用例 """
        form = AddCaseForm().do_validate()
        form.num.data = Case.get_insert_num(set_id=form.set_id.data)
        new_case = Case().create(form.data)
        return app.restful.success(f"用例【{new_case.name}】新建成功", data=new_case.to_dict())

    def put(self):
        """ 修改用例 """
        form = EditCaseForm().do_validate()
        CaseBusiness.put(form, Project, CaseSet, Case, Step)
        return app.restful.success(msg=f"用例【{form.case.name}】修改成功", data=form.case.to_dict())

    def delete(self):
        """ 删除用例 """
        form = DeleteCaseForm().do_validate()
        form.case.delete_current_and_step()
        return app.restful.success(f"用例【{form.case.name}】删除成功")


api_test.add_url_rule("/case", view_func=ApiCaseView.as_view("ApiCaseView"))
api_test.add_url_rule("/case/run", view_func=ApiRunCaseView.as_view("ApiRunCaseView"))
api_test.add_url_rule("/case/copy", view_func=ApiCopyCaseView.as_view("ApiCopyCaseView"))
api_test.add_url_rule("/case/list", view_func=ApiGetCaseListView.as_view("ApiGetCaseListView"))
api_test.add_url_rule("/case/sort", view_func=ApiChangeCaseSortView.as_view("ApiChangeCaseSortView"))
api_test.add_url_rule("/case/copy/step", view_func=ApiCopyCaseStepView.as_view("ApiCopyCaseStepView"))
api_test.add_url_rule("/case/pull/step", view_func=ApiPullCaseStepView.as_view("ApiPullCaseStepView"))
api_test.add_url_rule("/case/name", view_func=ApiGetCaseNameByIdView.as_view("ApiGetCaseNameByIdView"))
api_test.add_url_rule("/case/quote", view_func=ApiChangeCaseQuoteView.as_view("ApiChangeCaseQuoteView"))
api_test.add_url_rule("/case/changeIsRun", view_func=ApiChangeCaseStatusView.as_view("ApiChangeCaseStatusView"))
api_test.add_url_rule("/case/from", view_func=ApiGetQuoteCaseFromView.as_view("ApiGetQuoteCaseFromView"))
