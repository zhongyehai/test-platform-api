# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import app_test
from ...base_form import ChangeSortForm
from ...busines import RunCaseBusiness
from ..model_factory import AppUiReport as Report, AppUiCase as Case, AppUiCaseSuite as CaseSuite, AppUiTask as Task
from ..forms.task import RunTaskForm, AddTaskForm, EditTaskForm, GetTaskForm, DeleteTaskForm, \
    GetTaskListForm
from utils.client.run_ui_test import RunCase


@app_test.login_get("/task/list")
def app_get_task_list():
    """ 任务列表 """
    form = GetTaskListForm()
    if form.detail:
        get_filed = [
            Task.id, Task.name, Task.cron, Task.skip_holiday, Task.status, Task.project_id, Task.merge_notify,
            Task.push_hit, Task.create_user
        ]
    else:
        get_filed = Task.get_simple_filed_list()
    return app.restful.get_success(Task.make_pagination(form, get_filed=get_filed))


@app_test.login_put("/task/sort")
def app_change_task_sort():
    """ 更新定时任务的排序 """
    form = ChangeSortForm()
    Task.change_sort(**form.model_dump())
    return app.restful.change_success()


@app_test.login_post("/task/copy")
def app_copy_task():
    """ 复制任务 """
    form = GetTaskForm()
    form.task.copy()
    return app.restful.copy_success()


@app_test.login_get("/task")
def app_get_task():
    """ 获取定时任务 """
    return app.restful.success(data=GetTaskForm().task.to_dict())


@app_test.login_post("/task")
def app_add_task():
    """ 新增定时任务 """
    form = AddTaskForm()
    Task.model_create(form.model_dump())
    return app.restful.add_success()


@app_test.login_put("/task")
def app_change_task():
    """ 修改定时任务 """
    form = EditTaskForm()
    form.task.model_update(form.model_dump())
    form.task.update_task_to_memory()
    return app.restful.change_success()


@app_test.login_delete("/task")
def app_delete_task():
    """ 删除定时任务 """
    form = DeleteTaskForm()
    form.task.delete_task_to_memory()
    form.task.delete()
    return app.restful.delete_success()


@app_test.login_post("/task/status")
def app_enable_task():
    """ 启用任务 """
    form = GetTaskForm()
    res = form.task.enable_task()
    if res["status"] == 1:
        return app.restful.success(f"任务【{form.task.name}】启用成功", data=res["data"])
    else:
        return app.restful.fail(f"任务【{form.task.name}】启用失败", data=res["data"])


@app_test.login_delete("/task/status")
def app_disable_task():
    """ 禁用任务 """
    form = GetTaskForm()
    res = form.task.disable_task()
    if res["status"] == 1:
        return app.restful.success(f"任务【{form.task.name}】禁用成功", data=res["data"])
    else:
        return app.restful.fail(f"任务【{form.task.name}】禁用失败", data=res["data"])


@app_test.post("/task/run")
def app_run_task():
    """ 单次运行定时任务 """
    form = RunTaskForm()
    form.env_list = form.env_list or form.task.env_list
    case_id_list = CaseSuite.get_case_id(Case, form.task.project_id, form.task.suite_ids, form.task.case_ids)
    appium_config = RunCaseBusiness.get_appium_config(form.task.project_id, form)
    batch_id = Report.get_batch_id()
    report_id = RunCaseBusiness.run(
        project_id=form.task.project_id,
        batch_id=batch_id,
        report_name=form.task.name,
        report_model=Report,
        env_code=form.env_list[0],
        trigger_type=form.trigger_type,
        is_async=form.is_async,
        task_type="task",
        trigger_id=form.id,
        case_id_list=case_id_list,
        run_type="app",
        runner=RunCase,
        extend_data=form.extend,
        task_dict=form.task.to_dict(),
        appium_config=appium_config
    )
    return app.restful.trigger_success({"batch_id": batch_id, "report_id": report_id})
