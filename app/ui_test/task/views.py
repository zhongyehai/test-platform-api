# -*- coding: utf-8 -*-
from threading import Thread

import requests
from flask import request
from flask_login import current_user

from ..report.models import UiReport
from ..caseSet.models import UiCaeSet
from app.utils import restful
from app.utils.required import login_required
from app.utils.runUiTest.runUiTestRunner import RunCase
from app.ui_test import ui_test
from app.baseView import BaseMethodView
from app.baseModel import db
from .models import UiTask
from .forms import RunTaskForm, AddTaskForm, EditTaskForm, HasTaskIdForm, DeleteTaskIdForm, GetTaskListForm


@ui_test.route('/task/run', methods=['POST'])
@login_required
def ui_run_task_view():
    """ 单次运行定时任务 """
    form = RunTaskForm()
    if form.validate():
        task = form.task
        project_id = task.project_id
        report = UiReport.get_new_report(task.name, 'task', current_user.name, current_user.id, project_id)

        # 新起线程运行任务
        Thread(
            target=RunCase(
                project_id=project_id,
                report_id=report.id,
                run_name=report.name,
                task=task.to_dict(),
                case_id=UiCaeSet.get_case_id(project_id, task.loads(task.set_id), task.loads(task.case_id)),
                is_async=form.is_async.data,
                env=form.env.data
            ).run_case
        ).start()
        return restful.success(msg='触发执行成功，请等待执行完毕', data={'report_id': report.id})
    return restful.fail(form.get_error())


@ui_test.route('/task/list', methods=['GET'])
@login_required
def ui_task_list():
    """ 任务列表 """
    form = GetTaskListForm()
    if form.validate():
        return restful.success(data=UiTask.make_pagination(form))
    return restful.fail(form.get_error())


@ui_test.route('/task/sort', methods=['put'])
@login_required
def ui_change_task_sort():
    """ 更新定时任务的排序 """
    UiTask.change_sort(request.json.get('List'), request.json.get('pageNum'), request.json.get('pageSize'))
    return restful.success(msg='修改排序成功')


@ui_test.route('/task/copy', methods=['POST'])
@login_required
def ui_task_copy():
    """ 复制任务 """
    form = HasTaskIdForm()
    if form.validate():
        old_task = form.task
        with db.auto_commit():
            new_task = UiTask()
            new_task.create(old_task.to_dict(), 'set_id', 'case_id')
            new_task.name = old_task.name + '_copy'
            new_task.status = 0
            new_task.num = UiTask.get_insert_num(project_id=old_task.project_id)
            db.session.add(new_task)
        return restful.success(msg='复制成功', data=new_task.to_dict())
    return restful.fail(form.get_error())


class UiTaskView(BaseMethodView):
    """ 任务管理 """

    def get(self):
        form = HasTaskIdForm()
        if form.validate():
            return restful.success(data=form.task.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        form = AddTaskForm()
        if form.validate():
            form.num.data = UiTask.get_insert_num(project_id=form.project_id.data)
            new_task = UiTask().create(form.data, 'set_id', 'case_id')
            return restful.success(f'任务【{form.name.data}】新建成功', new_task.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditTaskForm()
        if form.validate():
            form.num.data = UiTask.get_insert_num(project_id=form.project_id.data)
            form.task.update(form.data, 'set_id', 'case_id')
            return restful.success(f'任务【{form.name.data}】修改成功', form.task.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteTaskIdForm()
        if form.validate():
            form.task.delete()
            return restful.success(f'任务【{form.task.name}】删除成功')
        return restful.fail(form.get_error())


class UiTaskStatus(BaseMethodView):
    """ 任务状态修改 """

    def post(self):
        """ 启用任务 """
        form = HasTaskIdForm()
        if form.validate():
            task = form.task
            try:
                res = requests.post(
                    url='http://localhost:8025/api/job/status',
                    json={'userId': current_user.id, 'taskId': task.id, 'type': 'ui'}
                ).json()
                if res["status"] == 200:
                    return restful.success(f'任务【{form.task.name}】启用成功', data=res)
                else:
                    return restful.fail(f'任务【{form.task.name}】启用失败', data=res)
            except Exception as error:
                return restful.fail(f'任务【{form.task.name}】启用失败', data=error)
        return restful.fail(form.get_error())

    def delete(self):
        """ 禁用任务 """
        form = HasTaskIdForm()
        if form.validate():
            if form.task.status != 1:
                return restful.fail(f'任务【{form.task.name}】的状态不为启用中')
            try:
                res = requests.delete(
                    url='http://localhost:8025/api/job/status',
                    json={'taskId': form.task.id, 'type': 'ui'}
                ).json()
                if res["status"] == 200:
                    return restful.success(f'任务【{form.task.name}】禁用成功', data=res)
                else:
                    return restful.fail(f'任务【{form.task.name}】禁用失败', data=res)
            except Exception as error:
                return restful.fail(f'任务【{form.task.name}】禁用失败', data=error)
        return restful.fail(form.get_error())


ui_test.add_url_rule('/task', view_func=UiTaskView.as_view('ui_task'))
ui_test.add_url_rule('/task/status', view_func=UiTaskStatus.as_view('ui_task_status'))
