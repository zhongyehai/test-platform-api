# -*- coding: utf-8 -*-
from flask import request, current_app as app, send_from_directory

from app.busines import RunCaseBusiness, CaseSuiteBusiness
from app.web_ui_test.models.case import WebUiCase as Case
from app.web_ui_test.models.report import WebUiReport as Report
from app.web_ui_test.blueprint import ui_test
from app.web_ui_test.models.suite import WebUiCaseSuite as CaseSuite
from app.web_ui_test.forms.suite import AddCaseSuiteForm, EditCaseSuiteForm, FindCaseSuite, GetCaseSuiteForm, \
    DeleteCaseSuiteForm, RunCaseSuiteForm
from utils.client.runUiTest import RunCase
from utils.util.fileUtil import STATIC_ADDRESS


@ui_test.login_get("/suite/template/download")
def ui_get_case_suite_template():
    """ 获取用例集导入模板 """
    return send_from_directory(STATIC_ADDRESS, "用例集导入模板.xmind", as_attachment=True)


@ui_test.login_post("/suite/upload")
def ui_case_suite_upload():
    """ 导入用例集 """
    project_id, file = request.form.get("project_id"), request.files.get("file")
    if project_id is None:
        return app.restful.fail("服务必传")
    if file and file.filename.endswith("xmind"):
        upload_res = CaseSuiteBusiness.upload_case_suite(project_id, file, CaseSuite, Case)
        return app.restful.success("导入完成", upload_res)
    return app.restful.fail("文件格式错误")


@ui_test.login_post("/suite/list")
def ui_get_case_suite_list():
    """ 用例集list """
    form = FindCaseSuite().do_validate()
    return app.restful.success(data=CaseSuite.make_pagination(form))


@ui_test.login_get("/suite")
def ui_get_case_suite():
    """ 获取用例集 """
    form = GetCaseSuiteForm().do_validate()
    return app.restful.success(data=form.suite.to_dict())


@ui_test.login_post("/suite")
def ui_add_case_suite():
    """ 新增用例集 """
    form = AddCaseSuiteForm().do_validate()
    form.num.data = CaseSuite.get_insert_num(project_id=form.project_id.data)
    new_suite = CaseSuite().create(form.data)
    return app.restful.success(f"用例集【{form.name.data}】创建成功", new_suite.to_dict())


@ui_test.login_put("/suite")
def ui_change_case_suite():
    """ 修改用例集 """
    form = EditCaseSuiteForm().do_validate()
    form.suite.update(form.data)
    if form.is_update_suite_type: form.suite.update_children_suite_type()
    return app.restful.success(f"用例集【{form.name.data}】修改成功", form.suite.to_dict())


@ui_test.login_delete("/suite")
def ui_delete_case_suite():
    """ 删除用例集 """
    form = DeleteCaseSuiteForm().do_validate()
    form.suite.delete()
    return app.restful.success("删除成功")


@ui_test.login_post("/suite/run")
def ui_run_case_suite():
    """ 运行用例集下的用例 """
    form = RunCaseSuiteForm().do_validate()
    batch_id = Report.get_batch_id()
    for env_code in form.env_list.data:
        report_id = RunCaseBusiness.run(
            batch_id=batch_id,
            env_code=env_code,
            browser=form.browser.data,
            is_async=form.is_async.data,
            project_id=form.suite.project_id,
            report_name=form.suite.name,
            task_type="suite",
            report_model=Report,
            trigger_id=form.id.data,
            case_id=form.suite.get_run_case_id(Case),
            run_type="webUi",
            run_func=RunCase
        )
    return app.restful.success(
        msg="触发执行成功，请等待执行完毕",
        data={
            "batch_id": batch_id,
            "report_id": report_id if len(form.env_list.data) == 1 else None
        })
