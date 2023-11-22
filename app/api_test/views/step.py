# -*- coding: utf-8 -*-
from flask import current_app as app

from ...base_form import ChangeSortForm
from ..blueprint import api_test
from ..model_factory import ApiStep as Step, ApiCase as Case
from ..forms.step import GetStepListForm, GetStepForm, AddStepForm, EditStepForm, DeleteStepForm, \
    ChangeStepStatusForm, CopyStepForm


@api_test.login_get("/step/list")
def api_get_step_list():
    """ 根据用例id获取步骤列表 """
    form = GetStepListForm()
    step_obj_list = Step.query.filter_by(case_id=form.case_id).order_by(Step.num.asc()).all()
    step_list = Step.set_has_step_for_step(step_obj_list, Case)
    return app.restful.get_success({"total": step_list.__len__(), "data": step_list})


@api_test.login_put("/step/sort")
def api_change_step_sort():
    """ 更新步骤的排序 """
    form = ChangeSortForm()
    Step.change_sort(**form.model_dump())
    return app.restful.change_success()


@api_test.login_put("/step/status")
def api_change_step_status():
    """ 修改步骤状态（是否执行） """
    form = ChangeStepStatusForm()
    Step.query.filter(Step.id.in_(form.id_list)).update({"status": form.status.value})
    return app.restful.change_success()


# @api_test.login_put("/step/host")
# def api_change_step_host():
#     """ 修改步骤引用的host """
#     step = Step.get_first(id=request.json.get("id"))
#     step.model_update(request.json)
#     return app.restful.success(
#         f'步骤已修改为 {"使用【用例】所在服务的host" if request.json.get("replace_host") else "使用【接口】所在服务的host"}',
#         data=step.to_dict()
#     )


@api_test.login_post("/step/copy")
def api_change_step_copy():
    """ 复制步骤 """
    form = CopyStepForm()
    step = Step.copy_step(form.id, form.case_id, Case)
    return app.restful.copy_success(step.to_dict())


@api_test.login_get("/step")
def api_get_step():
    """ 获取步骤 """
    form = GetStepForm()
    return app.restful.get_success(form.step.to_dict())


@api_test.login_post("/step")
def api_add_step():
    """ 新增步骤 """
    form = AddStepForm()
    Step.add_step(form.model_dump(), Case)
    return app.restful.add_success()


@api_test.login_put("/step")
def api_change_step():
    """ 修改步骤 """
    form = EditStepForm()
    form.step.model_update(form.model_dump())
    Case.merge_output(form.step.case_id, [form.step])  # 合并出参
    return app.restful.change_success()


@api_test.login_delete("/step")
def api_delete_step():
    """ 删除步骤 """
    form = DeleteStepForm()
    Step.query.filter(Step.id.in_(form.id_list)).delete()
    return app.restful.delete_success()
