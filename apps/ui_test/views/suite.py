# -*- coding: utf-8 -*-
from flask import request, current_app as app, send_from_directory

from ..blueprint import ui_test
from ...busines import RunCaseBusiness
from ..model_factory import WebUiCase as Case, WebUiReport as Report, WebUiCaseSuite as CaseSuite
from ..forms.suite import AddCaseSuiteForm, EditCaseSuiteForm, GetCaseSuiteListForm, GetCaseSuiteForm, \
    DeleteCaseSuiteForm, RunCaseSuiteForm
from utils.client.run_ui_test import RunCase
from utils.util.file_util import STATIC_ADDRESS


@ui_test.login_get("/suite/template/download")
def ui_get_case_suite_template():
    """ 获取用例集导入模板 """
    return send_from_directory(STATIC_ADDRESS, "case_suite_upload_template.xmind", as_attachment=True)


@ui_test.login_post("/suite/upload")
def ui_case_suite_upload():
    """ 导入用例集 """
    project_id, file = request.form.get("project_id"), request.files.get("file")
    if project_id is None:
        return app.restful.fail("服务必传")
    if file and file.filename.endswith("xmind"):
        upload_res = CaseSuite.upload_case_suite(project_id, file, Case)
        return app.restful.success("导入完成", upload_res)
    return app.restful.fail("文件格式错误")


@ui_test.login_get("/suite/list")
def ui_get_case_suite_list():
    """ 用例集list """
    form = GetCaseSuiteListForm()
    get_filed = [CaseSuite.id, CaseSuite.name, CaseSuite.parent, CaseSuite.project_id, CaseSuite.suite_type]
    return app.restful.get_success(CaseSuite.make_pagination(form, get_filed=get_filed))


@ui_test.login_get("/suite")
def ui_get_case_suite():
    """ 获取用例集 """
    form = GetCaseSuiteForm()
    return app.restful.get_success(form.suite.to_dict())


@ui_test.login_post("/suite")
def ui_add_case_suite():
    """ 新增用例集 """
    form = AddCaseSuiteForm()
    if len(form.data_list) == 1:
        return app.restful.add_success(CaseSuite.model_create_and_get(form.data_list[0]).to_dict())
    CaseSuite.model_batch_create(form.data_list)
    return app.restful.add_success()


@ui_test.login_put("/suite")
def ui_change_case_suite():
    """ 修改用例集 """
    form = EditCaseSuiteForm()
    form.suite.model_update(form.model_dump())
    if form.is_update_suite_type: form.suite.update_children_suite_type()
    return app.restful.change_success(form.suite.to_dict())


@ui_test.login_delete("/suite")
def ui_delete_case_suite():
    """ 删除用例集 """
    form = DeleteCaseSuiteForm()
    CaseSuite.delete_by_id(form.id)
    return app.restful.delete_success()


@ui_test.login_post("/suite/run")
def ui_run_case_suite():
    """ 运行用例集下的用例 """
    form = RunCaseSuiteForm()
    batch_id = Report.get_batch_id()
    case_id_list = form.suite.get_run_case_id(Case)
    for env_code in form.env_list:
        report_id = RunCaseBusiness.run(
            project_id=form.suite.project_id,
            batch_id=batch_id,
            trigger_id=form.id,
            report_model=Report,
            env_code=env_code,
            browser=form.browser,
            is_async=form.is_async,
            report_name=form.suite.name,
            task_type="suite",
            case_id_list=case_id_list,
            run_type="ui",
            runner=RunCase
        )
    return app.restful.trigger_success({
        "batch_id": batch_id,
        "report_id": report_id if len(form.env_list) == 1 else None
    })
