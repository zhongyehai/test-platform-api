# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import api_test
from apps.busines import RunCaseBusiness
from ..model_factory import ApiProject as Project, ApiCase as Case, ApiStep as Step, ApiReport as Report, \
    ApiCaseSuite as CaseSuite
from ..forms.case import AddCaseForm, EditCaseForm, GetCaseListForm, DeleteCaseForm, GetCaseForm, RunCaseForm, \
    CopyCaseStepForm, PullCaseStepForm, ChangeCaseStatusForm, GetAssistCaseForm, GetCaseNameForm
from utils.client.run_api_test import RunCase
from ...base_form import ChangeSortForm, ChangeCaseParentForm
from ...enums import ApiCaseSuiteTypeEnum


@api_test.login_get("/case/list")
def api_get_case_list():
    """ 根据模块获取用例list """
    form = GetCaseListForm()
    if form.detail:
        get_filed = [Case.id, Case.name, Case.desc, Case.status, Case.skip_if, Case.variables, Case.headers,
                     Case.output, Case.suite_id, Case.run_times, Case.create_user, Case.update_user]
    else:
        get_filed = Case.get_simple_filed_list()
    pagination_data = Case.make_pagination(form, get_filed=get_filed)

    if form.has_step:
        total, data_list = pagination_data["total"], Step.set_has_step_for_case(pagination_data["data"])
        return app.restful.get_success({"total": total, "data": data_list})
    return app.restful.get_success(pagination_data)


@api_test.login_put("/case/sort")
def api_change_case_sort():
    """ 更新用例的排序 """
    form = ChangeSortForm()
    Case.change_sort(**form.model_dump())
    return app.restful.change_success()


@api_test.login_get("/case/make-data-list")
def api_get_make_data_case_list():
    """ 根据服务id获取造数用例集下的用例list """
    form = GetAssistCaseForm()
    filed_list = ["id", "name", "desc", "status", "skip_if", "headers", "variables", "output", "suite_id"]
    case_list = Case.db.session.query(
        Case.id, Case.name, Case.desc, Case.status, Case.skip_if, Case.headers, Case.variables, Case.output,
        Case.suite_id
    ).filter(
        CaseSuite.project_id == form.project_id,
        CaseSuite.suite_type == ApiCaseSuiteTypeEnum.make_data,
        Case.suite_id == CaseSuite.id,
        Case.status == 1
    ).order_by(Case.num).all()
    return app.restful.get_success({
        "total": len(case_list),
        "data": [dict(zip(filed_list, case)) for case in case_list]
    })


@api_test.login_get("/case/name")
def api_get_case_name():
    """ 根据用例id获取用例名 """
    form = GetCaseNameForm()
    filed_list = ["id", "name"]
    case_list = Case.db.session.query(Case.id, Case.name).filterr(Case.id.in_(form.case_list)).all()
    return app.restful.get_success([dict(zip(filed_list, case)) for case in case_list])


@api_test.login_get("/case/project")
def api_get_case_from_project():
    """ 获取用例属于哪个用例集、哪个服务 """
    form = GetCaseForm()
    suite = CaseSuite.get_first(id=form.case.suite_id)
    project = Project.get_first(id=suite.project_id)
    return app.restful.get_success({
        "case": form.case.to_dict(),
        "suite": suite.to_dict(),
        "project": project.to_dict()
    })


@api_test.login_put("/case/status")
def api_change_case_status():
    """ 修改用例状态（是否执行） """
    form = ChangeCaseStatusForm()
    Case.query.filter(Case.id.in_(form.id_list)).update({'status': form.status.value})
    return app.restful.change_success()


@api_test.login_put("/case/parent")
def api_change_case_parent():
    """ 修改用例归属 """
    form = ChangeCaseParentForm()
    Case.query.filter(Case.id.in_(form.id_list)).update({'suite_id': form.suite_id})
    return app.restful.change_success()


@api_test.login_post("/case/copy")
def api_copy_case():
    """ 复制用例 """
    form = GetCaseForm()
    data = form.case.copy_case(Step)
    return app.restful.copy_success(data)


@api_test.login_post("/case/copy-step")
def api_copy_case_step():
    """ 复制指定用例的步骤到当前用例下 """
    form = CopyCaseStepForm()
    Case.copy_case_all_step_to_current_case(form, Step)
    Case.merge_variables(form.from_case, form.to_case)
    return app.restful.success("步骤拉取成功，自定义变量已合并至当前用例")


@api_test.login_get("/case/from")
def api_get_case_from():
    """ 获取用例的归属 """
    form = GetCaseForm()
    from_path = form.case.get_quote_case_from(Project, CaseSuite)
    return app.restful.get_success(from_path)


@api_test.login_get("/case")
def api_get_case():
    """ 获取用例 """
    form = GetCaseForm()
    return app.restful.get_success(form.case.to_dict())


@api_test.login_post("/case")
def api_add_case():
    """ 新增用例 """
    form = AddCaseForm()
    if len(form.case_list) == 1:
        return app.restful.add_success(Case.model_create_and_get(form.case_list[0]).to_dict())
    Case.model_batch_create(form.case_list)
    return app.restful.add_success()


@api_test.login_put("/case")
def api_change_case():
    """ 修改用例 """
    form = EditCaseForm()
    Case.query.filter_by(id=form.id).update(form.model_dump())
    return app.restful.change_success()


@api_test.login_delete("/case")
def api_delete_case():
    """ 删除用例 """
    form = DeleteCaseForm()
    Case.delete_by_id(form.id_list)
    return app.restful.delete_success()


@api_test.login_post("/case/run")
def api_run_case():
    """ 运行测试用例，并生成报告 """
    form = RunCaseForm()
    case_query = CaseSuite.db.session.query(Case.name, CaseSuite.project_id).filter(
        Case.id.in_(form.case_id_list), CaseSuite.id == Case.suite_id).first()
    batch_id = Report.get_batch_id()
    for env_code in form.env_list:
        report_id = RunCaseBusiness.run(
            project_id=case_query[1],
            batch_id=batch_id,
            report_name=case_query[0],
            report_model=Report,
            env_code=env_code,
            is_async=form.is_async,
            temp_variables=form.temp_variables,
            task_type="case",
            case_id_list=form.case_id_list,
            runner=RunCase
        )
    return app.restful.trigger_success({
        "batch_id": batch_id,
        "report_id": report_id if len(form.env_list) == 1 else None
    })
