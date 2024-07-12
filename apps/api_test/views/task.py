# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import api_test
from ...base_form import ChangeSortForm
from ...busines import RunCaseBusiness
from ..model_factory import ApiReport as Report, ApiCase as Case, ApiCaseSuite as CaseSuite, ApiTask as Task
from ..forms.task import RunTaskForm, AddTaskForm, EditTaskForm, GetTaskForm, DeleteTaskForm, \
    GetTaskListForm
from utils.client.run_api_test import RunCase


@api_test.login_get("/task/list")
def api_get_task_list():
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


@api_test.login_put("/task/sort")
def api_change_task_sort():
    """ 更新定时任务的排序 """
    form = ChangeSortForm()
    Task.change_sort(**form.model_dump())
    return app.restful.change_success()


@api_test.login_post("/task/copy")
def api_copy_task():
    """ 复制定时任务 """
    form = GetTaskForm()
    form.task.copy()
    return app.restful.copy_success()


@api_test.login_get("/task")
def api_get_task():
    """ 获取定时任务 """
    return app.restful.success(data=GetTaskForm().task.to_dict())


@api_test.login_post("/task")
def api_add_task():
    """ 新增定时任务 """
    form = AddTaskForm()
    Task.model_create(form.model_dump())
    return app.restful.add_success()


@api_test.login_put("/task")
def api_change_task():
    """ 修改定时任务 """
    form = EditTaskForm()
    form.task.model_update(form.model_dump())
    form.task.update_task_to_memory()
    return app.restful.change_success()


@api_test.login_delete("/task")
def api_delete_task():
    """ 删除定时任务 """
    form = DeleteTaskForm()
    form.task.delete_task_to_memory()
    form.task.delete()
    return app.restful.delete_success()


@api_test.login_post("/task/status")
def api_enable_task():
    """ 启用定时任务 """
    form = GetTaskForm()
    res = form.task.enable_task()
    if res["status"] == 1:
        return app.restful.success(f"任务【{form.task.name}】启用成功", data=res["data"])
    else:
        return app.restful.fail(f"任务【{form.task.name}】启用失败", data=res["data"])


@api_test.login_delete("/task/status")
def api_disable_task():
    """ 禁用定时任务 """
    form = GetTaskForm()
    res = form.task.disable_task()
    if res["status"] == 1:
        return app.restful.success(f"任务【{form.task.name}】禁用成功", data=res["data"])
    else:
        return app.restful.fail(f"任务【{form.task.name}】禁用失败", data=res["data"])


@api_test.post("/task/run")
def api_run_task():
    """ 运行定时任务 """
    form = RunTaskForm()
    case_id_list = CaseSuite.get_case_id(Case, form.task.project_id, form.task.suite_ids, form.task.case_ids)
    batch_id = Report.get_batch_id()
    env_list = form.env_list or form.task.env_list
    for env_code in env_list:
        report_id = RunCaseBusiness.run(
            project_id=form.task.project_id,
            batch_id=batch_id,
            report_name=form.task.name,
            report_model=Report,
            env_code=env_code,
            trigger_type=form.trigger_type,
            is_async=form.is_async,
            task_type="task",
            trigger_id=[form.id],
            case_id_list=case_id_list,
            run_type="api",
            runner=RunCase,
            task_dict=form.task.to_dict(),
            extend_data=form.extend
        )
    return app.restful.trigger_success({
        "batch_id": batch_id,
        "report_id": report_id if len(env_list) == 1 else None
    })
