# -*- coding: utf-8 -*-
from selenium.webdriver.common.keys import Keys
from flask import current_app as app

from ...base_form import ChangeSortForm
from ..blueprint import ui_test
from ..model_factory import WebUiStep as Step, WebUiCase as Case
from ..forms.step import GetStepListForm, GetStepForm, AddStepForm, EditStepForm, ChangeStepStatusForm, \
    DeleteStepForm, CopyStepForm
from config import ui_action_mapping_list, ui_assert_mapping_list, ui_extract_mapping_list


@ui_test.login_get("/step/executeMapping")
def ui_get_step_execute_mapping():
    """ 获取执行动作类型列表 """
    return app.restful.get_success(ui_action_mapping_list)


@ui_test.login_get("/step/extractMapping")
def ui_get_step_extract_mapping():
    """ 数据提取方法列表 """
    return app.restful.get_success(ui_extract_mapping_list)


@ui_test.login_get("/step/assertMapping")
def ui_get_step_assert_mapping():
    """ 断言方法列表 """
    return app.restful.get_success(ui_assert_mapping_list)


@ui_test.login_get("/step/keyBoardCode")
def ui_get_step_key_board_code():
    """ 获取键盘映射 """
    data = {key: f'按键【{key}】' for key in dir(Keys) if key.startswith('_') is False}
    return app.restful.get_success(data)


@ui_test.login_get("/step/list")
def ui_get_step_list():
    """ 根据用例id获取步骤列表 """
    form = GetStepListForm()
    step_obj_list = Step.query.filter_by(case_id=form.case_id).order_by(Step.num.asc()).all()
    step_list = Step.set_has_step_for_step(step_obj_list, Case)
    return app.restful.get_success({"total": step_list.__len__(), "data": step_list})


@ui_test.login_put("/step/sort")
def ui_change_step_sort():
    """ 更新步骤的排序 """
    form = ChangeSortForm()
    Step.change_sort(**form.model_dump())
    return app.restful.change_success()


@ui_test.login_put("/step/status")
def ui_change_step_status():
    """ 修改步骤状态（是否执行） """
    form = ChangeStepStatusForm()
    Step.query.filter(Step.id.in_(form.id_list)).update({"status": form.status.value})
    return app.restful.change_success()


@ui_test.login_post("/step/copy")
def ui_change_step_copy():
    """ 复制步骤 """
    form = CopyStepForm()
    step = Step.copy_step(form.id, form.case_id, Case)
    return app.restful.copy_success(step.to_dict())


@ui_test.login_get("/step")
def ui_get_step():
    """ 获取步骤 """
    form = GetStepForm()
    return app.restful.get_success(form.step.to_dict())


@ui_test.login_post("/step")
def ui_add_step():
    """ 新增步骤 """
    form = AddStepForm()
    Step.add_step(form.model_dump(), Case)
    return app.restful.add_success()


@ui_test.login_put("/step")
def ui_change_step():
    """ 修改步骤 """
    form = EditStepForm()
    form.step.model_update(form.model_dump())
    Case.merge_output(form.step.case_id, [form.step])  # 合并出参
    return app.restful.change_success()


@ui_test.login_delete("/step")
def ui_delete_step():
    """ 删除步骤 """
    form = DeleteStepForm()
    Step.query.filter(Step.id.in_(form.id_list)).delete()
    return app.restful.delete_success()
