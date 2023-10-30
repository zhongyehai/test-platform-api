# -*- coding: utf-8 -*-
import json

from flask import request, current_app as app

from app.busines import RunCaseBusiness, CaseBusiness
from app.app_ui_test.blueprint import app_test
from utils.client.runUiTest import RunCase
from app.app_ui_test.models.project import AppUiProject as Project
from app.app_ui_test.models.case import AppUiCase as Case
from app.app_ui_test.models.step import AppUiStep as Step
from app.app_ui_test.models.report import AppUiReport as Report
from app.app_ui_test.models.suite import AppUiCaseSuite as CaseSuite
from app.app_ui_test.forms.case import AddCaseForm, EditCaseForm, FindCaseForm, DeleteCaseForm, GetCaseForm, \
    RunCaseForm, CopyCaseStepForm, PullCaseStepForm, ChangeCaseStatusForm


@app_test.login_get("/case/list")
def app_get_case_list():
    """ 根据用例集查找用例列表 """
    form = FindCaseForm().do_validate()
    data = Case.make_pagination(form)
    if form.getHasStep.data:
        total, data_list = data["total"], Step.set_has_step_for_case(data["data"])
        return app.restful.success(data={"total": total, "data": data_list})
    return app.restful.success(data=data)


@app_test.login_get("/case/name")
def app_get_case_name():
    """ 根据用例id获取用例名 """
    # caseId: "1,4,12"
    case_ids: list = request.args.to_dict().get("caseId").split(",")
    return app.restful.success(
        data=[{"id": int(case_id), "name": Case.get_first(id=case_id).name} for case_id in case_ids])


@app_test.login_put("/case/quote")
def app_change_case_quote():
    """ 更新用例引用 """
    case_id, quote_type, quote = request.json.get("id"), request.json.get("quoteType"), request.json.get("quote")
    Case.get_first(id=case_id).update({quote_type: json.dumps(quote)})
    return app.restful.success(msg="引用关系修改成功")


@app_test.login_get("/case/project")
def app_get_case_from_project():
    """ 获取用例属于哪个用例集、哪个服务 """
    case = Case.get_first(id=request.args.get("id"))
    suite = CaseSuite.get_first(id=case.suite_id)
    project = Project.get_first(id=suite.project_id)
    return app.restful.success(data={
        "case": case.to_dict(),
        "suite": suite.to_dict(),
        "project": project.to_dict()
    })


@app_test.login_put("/case/sort")
def app_change_case_sort():
    """ 更新用例的排序 """
    Case.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
    return app.restful.success(msg="修改排序成功")


@app_test.login_put("/case/status")
def app_change_case_status():
    """ 修改用例状态（是否执行） """
    form = ChangeCaseStatusForm().do_validate()
    for case in form.case_list:
        case.change_status(form.status.data)
    return app.restful.success("运行状态修改成功")


@app_test.login_post("/case/copy")
def app_copy_case():
    """ 复制用例 """
    form = GetCaseForm().do_validate()
    data = CaseBusiness.copy(form, Case, Step)
    return app.restful.success("复制成功", data=data)


@app_test.login_post("/case/copy/step")
def app_copy_case_step():
    """ 复制指定用例的步骤到当前用例下 """
    form = CopyCaseStepForm().do_validate()
    step_list = CaseBusiness.copy_case_all_step_to_current_case(form, Step, Case)
    Case.merge_variables(form.source.data, form.to.data)
    return app.restful.success("步骤拉取成功，自定义变量已合并至当前用例", data=step_list)


@app_test.login_post("/case/pull/step")
def app_pull_case_step():
    """ 复制指定用例的步骤到当前用例下 """
    form = PullCaseStepForm().do_validate()
    CaseBusiness.copy_step_to_current_case(form, Step)
    return app.restful.success("步骤复制成功")


@app_test.login_get("/case/from")
def app_get_case_from():
    """ 获取用例的归属 """
    form = GetCaseForm().do_validate()
    from_path = CaseBusiness.get_quote_case_from(form.id.data, Project, CaseSuite, Case)
    return app.restful.success("获取成功", data=from_path)


@app_test.login_get("/case")
def app_get_case():
    """ 获取用例 """
    form = GetCaseForm().do_validate()
    return app.restful.success("获取成功", data=form.case.to_dict())


@app_test.login_post("/case")
def app_add_case():
    """ 新增用例 """
    form = AddCaseForm().do_validate()
    for case in form.case_list.data:
        case["suite_id"] = form.suite_id.data
        case["num"] = Case.get_insert_num(suite_id=form.suite_id.data)
        new_case = Case().create(case)
    return app.restful.success(f"用例新建成功", data=new_case.to_dict() if len(form.case_list.data) == 1 else None)


@app_test.login_put("/case")
def app_change_case():
    """ 修改用例 """
    form = EditCaseForm().do_validate()
    form.case.update(form.data)
    return app.restful.success(msg=f"用例【{form.case.name}】修改成功", data=form.case.to_dict())


@app_test.login_delete("/case")
def app_delete_case():
    """ 删除用例 """
    form = DeleteCaseForm().do_validate()
    form.case.delete_current_and_step()
    return app.restful.success(f"用例【{form.case.name}】删除成功")


@app_test.login_post("/case/run")
def app_run_case():
    """ 运行测试用例 """
    form = RunCaseForm().do_validate()
    case = form.case_list[0]
    project_id = CaseSuite.get_first(id=case.suite_id).project_id
    appium_config = RunCaseBusiness.get_appium_config(project_id, form)
    batch_id = Report.get_batch_id()
    report_id = RunCaseBusiness.run(
        batch_id=batch_id,
        env_code=form.env_list.data[0],
        is_async=form.is_async.data,
        project_id=project_id,
        temp_variables=form.temp_variables.data,
        report_name=case.name,
        task_type="case",
        report_model=Report,
        case_id=form.caseId.data,
        run_type="app",
        run_func=RunCase,
        appium_config=appium_config
    )
    return app.restful.success(
        msg="触发执行成功，请等待执行完毕",
        data={
            "batch_id": batch_id,
            "report_id": report_id
        })
