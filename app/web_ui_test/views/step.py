# -*- coding: utf-8 -*-
from selenium.webdriver.common.keys import Keys
from flask import request, current_app as app

from app.busines import StepBusiness
from app.web_ui_test.blueprint import ui_test
from config import ui_action_mapping_list, ui_assert_mapping_list, ui_extract_mapping_list
from app.web_ui_test.models.step import WebUiStep as Step
from app.web_ui_test.models.case import WebUiCase as Case
from app.web_ui_test.forms.step import GetStepListForm, GetStepForm, AddStepForm, EditStepForm, ChangeStepStatusForm, \
    DeleteStepForm


@ui_test.login_get("/step/executeMapping")
def ui_get_step_execute_mapping():
    """ 获取执行动作类型列表 """
    return app.restful.success("获取成功", data=ui_action_mapping_list)


@ui_test.login_get("/step/extractMapping")
def ui_get_step_extract_mapping():
    """ 数据提取方法列表 """
    return app.restful.success("获取成功", data=ui_extract_mapping_list)


@ui_test.login_get("/step/assertMapping")
def ui_get_step_assert_mapping():
    """ 断言方法列表 """
    return app.restful.success("获取成功", data=ui_assert_mapping_list)


@ui_test.login_get("/step/keyBoardCode")
def ui_get_step_key_board_code():
    """ 获取键盘映射 """
    data = {key: f'按键【{key}】' for key in dir(Keys) if key.startswith('_') is False}
    return app.restful.success("获取成功", data=data)


@ui_test.login_get("/step/list")
def ui_get_step_list():
    """ 根据用例id获取步骤列表 """
    form = GetStepListForm().do_validate()
    step_obj_list = Step.query.filter_by(case_id=form.caseId.data).order_by(Step.num.asc()).all()
    step_list = Step.set_has_step_for_step(step_obj_list, Case)
    return app.restful.success("获取成功", data={"total": step_list.__len__(), "data": step_list})


@ui_test.login_put("/step/status")
def ui_change_step_status():
    """ 修改步骤状态（是否执行） """
    form = ChangeStepStatusForm().do_validate()
    for step in form.step_list:
        step.change_status(form.status.data)
    return app.restful.success("运行状态修改成功")


@ui_test.login_put("/step/sort")
def ui_change_step_sort():
    """ 更新步骤的排序 """
    Step.change_sort(request.json.get("List"), request.json.get("pageNum", 0), request.json.get("pageSize", 0))
    return app.restful.success(msg="修改排序成功")


@ui_test.login_post("/step/copy")
def ui_change_step_copy():
    """ 复制步骤 """
    step_id, case_id = request.json.get("id"), request.json.get("caseId")
    step = StepBusiness.copy(step_id, case_id, Step, Case)
    return app.restful.success(msg="步骤复制成功", data=step.to_dict())


@ui_test.login_get("/step")
def ui_get_step():
    """ 获取步骤 """
    form = GetStepForm().do_validate()
    return app.restful.success("获取成功", data=form.step.to_dict())


@ui_test.login_post("/step")
def ui_add_step():
    """ 新增步骤 """
    form = AddStepForm().do_validate()
    step = StepBusiness.post(form, Step, Case)
    return app.restful.success(
        f'步骤【{step.name}】新建成功{", 自定义变量已合并至当前用例，请处理" if step.quote_case else ""}',
        data=step.to_dict()
    )


@ui_test.login_put("/step")
def ui_change_step():
    """ 修改步骤 """
    form = EditStepForm().do_validate()
    form.step.update(form.data)
    Case.merge_output(form.step.case_id, [form.step])  # 合并出参
    return app.restful.success(msg=f"步骤【{form.step.name}】修改成功", data=form.step.to_dict())


@ui_test.login_delete("/step")
def ui_delete_step():
    """ 删除步骤 """
    form = DeleteStepForm().do_validate()
    for step in form.step_list:
        step.delete()
    return app.restful.success(f"步骤删除成功")
