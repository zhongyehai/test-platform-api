# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import ui_test
from ...base_form import ChangeSortForm
from ...busines import RunCaseBusiness
from ..model_factory import WebUiReport as Report, WebUiCase as Case, WebUiCaseSuite as CaseSuite, WebUiTask as Task
from ..forms.task import RunTaskForm, AddTaskForm, EditTaskForm, GetTaskForm, DeleteTaskForm, \
    GetTaskListForm
from utils.client.run_ui_test import RunCase
from ...config.models.config import Config
from ...system.models.user import User


@ui_test.login_get("/task/list")
def ui_get_task_list():
    """ 任务列表 """
    form = GetTaskListForm()
    if form.detail:
        get_filed = [
            Task.id, Task.name, Task.cron, Task.skip_holiday, Task.status, Task.project_id, Task.merge_notify,
            Task.push_hit, Task.create_user, Task.receive_type, Task.is_send, Task.env_list
        ]
    else:
        get_filed = Task.get_simple_filed_list()
    return app.restful.get_success(Task.make_pagination(form, get_filed=get_filed))


@ui_test.login_put("/task/sort")
def ui_change_task_sort():
    """ 更新定时任务的排序 """
    form = ChangeSortForm()
    Task.change_sort(**form.model_dump())
    return app.restful.change_success()


@ui_test.login_post("/task/copy")
def ui_copy_task():
    """ 复制任务 """
    form = GetTaskForm()
    form.task.copy()
    return app.restful.copy_success()


@ui_test.login_get("/task")
def ui_get_task():
    """ 获取定时任务 """
    return app.restful.success(data=GetTaskForm().task.to_dict())


@ui_test.login_post("/task")
def ui_add_task():
    """ 新增定时任务 """
    form = AddTaskForm()
    Task.model_create(form.model_dump())
    return app.restful.add_success()


@ui_test.login_put("/task")
def ui_change_task():
    """ 修改定时任务 """
    form = EditTaskForm()
    form.task.model_update(form.model_dump())
    form.task.update_task_to_memory()
    return app.restful.change_success()


@ui_test.login_delete("/task")
def ui_delete_task():
    """ 删除定时任务 """
    form = DeleteTaskForm()
    form.task.delete_task_to_memory()
    form.task.delete()
    return app.restful.delete_success()


@ui_test.login_post("/task/status")
def ui_enable_task():
    """ 启用任务 """
    form = GetTaskForm()
    res = form.task.enable_task()
    if res["status"] == 1:
        return app.restful.success(f"任务【{form.task.name}】启用成功", data=res["data"])
    else:
        return app.restful.fail(f"任务【{form.task.name}】启用失败", data=res["data"])


@ui_test.login_delete("/task/status")
def ui_disable_task():
    """ 禁用任务 """
    form = GetTaskForm()
    res = form.task.disable_task()
    if res["status"] == 1:
        return app.restful.success(f"任务【{form.task.name}】禁用成功", data=res["data"])
    else:
        return app.restful.fail(f"任务【{form.task.name}】禁用失败", data=res["data"])


@ui_test.post("/task/run")
def ui_run_task():
    """ 单次运行定时任务 """
    form = RunTaskForm()
    for task in form.task_list:
        case_id_list = CaseSuite.get_case_id(Case, task.project_id, task.suite_ids, task.case_ids)
        batch_id = Report.get_batch_id()
        env_list = form.env_list or task.env_list
        for env_code in env_list:
            report_id = RunCaseBusiness.run(
                batch_id=batch_id,
                env_code=env_code,
                browser=form.browser if hasattr(form, 'browser') else task.browser,
                trigger_type=form.trigger_type,
                is_async=form.is_async,
                project_id=task.project_id,
                report_name=task.name,
                task_type="task",
                report_model=Report,
                trigger_id=[task.id],
                case_id_list=case_id_list,
                run_type="ui",
                runner=RunCase,
                extend_data=form.extend,
                task_dict=task.to_dict()
            )
    return app.restful.trigger_success({
        "batch_id": batch_id,
        "report_id": report_id if len(env_list) == 1 else None
    })
