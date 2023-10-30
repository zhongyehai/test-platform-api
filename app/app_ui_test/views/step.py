# -*- coding: utf-8 -*-
from flask import request, current_app as app

from app.busines import StepBusiness
from app.app_ui_test.blueprint import app_test
from config import ui_action_mapping_list, ui_assert_mapping_list, ui_extract_mapping_list
from app.app_ui_test.models.step import AppUiStep as Step
from app.app_ui_test.models.case import AppUiCase as Case
from app.app_ui_test.forms.step import GetStepListForm, GetStepForm, AddStepForm, EditStepForm, ChangeStepStatusForm, \
    DeleteStepForm


@app_test.login_get("/step/executeMapping")
def app_get_step_execute_mapping():
    """ 获取执行动作类型列表 """
    return app.restful.success("获取成功", data=ui_action_mapping_list)


@app_test.login_get("/step/extractMapping")
def app_get_step_extract_mapping():
    """ 数据提取方法列表 """
    return app.restful.success("获取成功", data=ui_extract_mapping_list)


@app_test.login_get("/step/assertMapping")
def app_get_step_assert_mapping():
    """ 断言方法列表 """
    return app.restful.success("获取成功", data=ui_assert_mapping_list)


@app_test.login_get("/step/list")
def app_get_step_list():
    """ 根据用例id获取步骤列表 """
    form = GetStepListForm().do_validate()
    step_obj_list = Step.query.filter_by(case_id=form.caseId.data).order_by(Step.num.asc()).all()
    step_list = Step.set_has_step_for_step(step_obj_list, Case)
    return app.restful.success("获取成功", data={"total": step_list.__len__(), "data": step_list})


@app_test.login_put("/step/status")
def app_change_step_status():
    """ 修改步骤状态（是否执行） """
    form = ChangeStepStatusForm().do_validate()
    for step in form.step_list:
        step.change_status(form.status.data)
    return app.restful.success("运行状态修改成功")


@app_test.login_put("/step/sort")
def app_change_step_sort():
    """ 更新步骤的排序 """
    Step.change_sort(request.json.get("List"), request.json.get("pageNum", 0), request.json.get("pageSize", 0))
    return app.restful.success(msg="修改排序成功")


@app_test.login_post("/step/copy")
def app_change_step_copy():
    """ 复制步骤 """
    step_id, case_id = request.json.get("id"), request.json.get("caseId")
    step = StepBusiness.copy(step_id, case_id, Step, Case)
    return app.restful.success(msg="步骤复制成功", data=step.to_dict())


@app_test.login_get("/step")
def app_get_step():
    """ 获取步骤 """
    form = GetStepForm().do_validate()
    return app.restful.success("获取成功", data=form.step.to_dict())


@app_test.login_post("/step")
def app_add_step():
    """ 新增步骤 """
    form = AddStepForm().do_validate()
    step = StepBusiness.post(form, Step, Case)
    return app.restful.success(
        f'步骤【{step.name}】新建成功{", 自定义变量已合并至当前用例，请处理" if step.quote_case else ""}',
        data=step.to_dict()
    )


@app_test.login_put("/step")
def app_change_step():
    """ 修改步骤 """
    form = EditStepForm().do_validate()
    form.step.update(form.data)
    Case.merge_output(form.step.case_id, [form.step])  # 合并出参
    return app.restful.success(msg=f"步骤【{form.step.name}】修改成功", data=form.step.to_dict())


@app_test.login_delete("/step")
def app_delete_step():
    """ 删除步骤 """
    form = DeleteStepForm().do_validate()
    for step in form.step_list:
        step.delete()
    return app.restful.success(f"步骤删除成功")
