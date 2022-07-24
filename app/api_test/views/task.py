# -*- coding: utf-8 -*-
from threading import Thread

import requests
from flask import request, g

from app.api_test.models.report import ApiReport
from app.api_test.models.caseSet import ApiSet
from utils import restful
from utils.required import login_required
from utils.client.runApiTest.runHttpRunner import RunCase
from app.api_test import api_test
from app.baseView import BaseMethodView
from app.baseModel import db
from app.api_test.models.task import ApiTask
from app.api_test.forms.task import RunTaskForm, AddTaskForm, EditTaskForm, HasTaskIdForm, DeleteTaskIdForm, GetTaskListForm


@api_test.route('/task/run', methods=['POST'])
@login_required
def api_run_task_view():
    """ 单次运行定时任务 """
    form = RunTaskForm()
    if form.validate():
        task = form.task
        project_id = task.project_id
        report = ApiReport.get_new_report(task.name, 'task', g.user_name, g.user_id, project_id)

        # 新起线程运行任务
        Thread(
            target=RunCase(
                project_id=project_id,
                report_id=report.id,
                run_name=report.name,
                task=task.to_dict(),
                case_id=ApiSet.get_case_id(project_id, task.loads(task.set_ids), task.loads(task.case_ids)),
                is_async=form.is_async.data,
                env=form.env.data
            ).run_case
        ).start()
        return restful.success(msg='触发执行成功，请等待执行完毕', data={'report_id': report.id})
    return restful.fail(form.get_error())


@api_test.route('/task/list', methods=['GET'])
@login_required
def api_task_list():
    """ 任务列表 """
    form = GetTaskListForm()
    if form.validate():
        return restful.success(data=ApiTask.make_pagination(form))
    return restful.fail(form.get_error())


@api_test.route('/task/sort', methods=['put'])
@login_required
def api_change_task_sort():
    """ 更新定时任务的排序 """
    ApiTask.change_sort(request.json.get('List'), request.json.get('pageNum'), request.json.get('pageSize'))
    return restful.success(msg='修改排序成功')


@api_test.route('/task/copy', methods=['POST'])
@login_required
def api_task_copy():
    """ 复制任务 """
    form = HasTaskIdForm()
    if form.validate():
        old_task = form.task
        with db.auto_commit():
            new_task = ApiTask()
            new_task.create(old_task.to_dict())
            new_task.name = old_task.name + '_copy'
            new_task.status = 0
            new_task.num = ApiTask.get_insert_num(project_id=old_task.project_id)
            db.session.add(new_task)
        return restful.success(msg='复制成功', data=new_task.to_dict())
    return restful.fail(form.get_error())


class ApiTaskView(BaseMethodView):
    """ 任务管理 """

    def get(self):
        form = HasTaskIdForm()
        if form.validate():
            return restful.success(data=form.task.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        form = AddTaskForm()
        if form.validate():
            form.num.data = ApiTask.get_insert_num(project_id=form.project_id.data)
            new_task = ApiTask().create(form.data)
            return restful.success(f'任务【{form.name.data}】新建成功', new_task.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditTaskForm()
        if form.validate():
            form.num.data = ApiTask.get_insert_num(project_id=form.project_id.data)
            form.task.update(form.data)
            return restful.success(f'任务【{form.name.data}】修改成功', form.task.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteTaskIdForm()
        if form.validate():
            form.task.delete()
            return restful.success(f'任务【{form.task.name}】删除成功')
        return restful.fail(form.get_error())


class ApiTaskStatus(BaseMethodView):
    """ 任务状态修改 """

    def post(self):
        """ 启用任务 """
        form = HasTaskIdForm()
        if form.validate():
            task = form.task
            try:
                res = requests.post(
                    url='http://localhost:8025/api/job/status',
                    json={'userId': g.user_id, 'taskId': task.id, 'type': 'api'}
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
                    json={'taskId': form.task.id, 'type': 'api'}
                ).json()
                if res["status"] == 200:
                    return restful.success(f'任务【{form.task.name}】禁用成功', data=res)
                else:
                    return restful.fail(f'任务【{form.task.name}】禁用失败', data=res)
            except Exception as error:
                return restful.fail(f'任务【{form.task.name}】禁用失败', data=error)
        return restful.fail(form.get_error())


api_test.add_url_rule('/task', view_func=ApiTaskView.as_view('api_task'))
api_test.add_url_rule('/task/status', view_func=ApiTaskStatus.as_view('api_task_status'))
