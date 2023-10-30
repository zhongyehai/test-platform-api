# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.api_test.blueprint import api_test
from app.api_test.models.step import ApiStep as Step
from app.api_test.models.case import ApiCase as Case
from app.api_test.forms.step import GetStepListForm, GetStepForm, AddStepForm, EditStepForm, DeleteStepForm, \
    ChangeStepStatusForm
from app.busines import StepBusiness


@api_test.login_get("/step/list")
def api_get_step_list():
    """ 根据用例id获取步骤列表 """
    form = GetStepListForm().do_validate()
    step_obj_list = Step.query.filter_by(case_id=form.caseId.data).order_by(Step.num.asc()).all()
    step_list = Step.set_has_step_for_step(step_obj_list, Case)
    return app.restful.success("获取成功", data={"total": step_list.__len__(), "data": step_list})


@api_test.login_put("/step/status")
def api_change_step_status():
    """ 修改步骤状态（是否执行） """
    form = ChangeStepStatusForm().do_validate()
    for step in form.step_list:
        step.change_status(form.status.data)
    return app.restful.success("运行状态修改成功")


@api_test.login_put("/step/host")
def api_change_step_host():
    """ 修改步骤引用的host """
    step = Step.get_first(id=request.json.get("id"))
    step.update(request.json)
    return app.restful.success(
        f'步骤已修改为 {"使用【用例】所在服务的host" if request.json.get("replace_host") else "使用【接口】所在服务的host"}',
        data=step.to_dict()
    )


@api_test.login_put("/step/sort")
def api_change_step_sort():
    """ 更新步骤的排序 """
    Step.change_sort(request.json.get("List"), request.json.get("pageNum", 0), request.json.get("pageSize", 0))
    return app.restful.success(msg="修改排序成功")


@api_test.login_post("/step/copy")
def api_change_step_copy():
    """ 复制步骤 """
    step_id, case_id = request.json.get("id"), request.json.get("caseId")
    step = StepBusiness.copy(step_id, case_id, Step, Case, step_type="api")
    return app.restful.success(msg="步骤复制成功", data=step.to_dict())


@api_test.login_get("/step")
def api_get_step():
    """ 获取步骤 """
    form = GetStepForm().do_validate()
    return app.restful.success("获取成功", data=form.step.to_dict())


@api_test.login_post("/step")
def api_add_step():
    """ 新增步骤 """
    form = AddStepForm().do_validate()
    step = StepBusiness.post(form, Step, Case, step_type="api")
    return app.restful.success(
        f'步骤【{step.name}】新建成功{", 自定义变量已合并至当前用例" if step.quote_case else ""}',
        data=step.to_dict()
    )


@api_test.login_put("/step")
def api_change_step():
    """ 修改步骤 """
    form = EditStepForm().do_validate()
    form.step.update(form.data)
    Case.merge_output(form.step.case_id, [form.step])  # 合并出参
    return app.restful.success(msg=f"步骤【{form.step.name}】修改成功", data=form.step.to_dict())


@api_test.login_delete("/step")
def api_delete_step():
    """ 删除步骤 """
    form = DeleteStepForm().do_validate()
    for step in form.step_list:
        step.delete()
        step.subtract_api_quote_count()
    return app.restful.success(f"步骤删除成功")
