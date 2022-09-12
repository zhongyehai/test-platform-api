# -*- coding: utf-8 -*-
from threading import Thread

import requests
from flask import current_app as app, request, g

from app.api_test.models.report import ApiReport
from app.api_test.models.caseSet import ApiSet
from app.baseView import LoginRequiredView
from utils.client.runApiTest.runHttpRunner import RunCase
from app.api_test import api_test
from app.baseModel import db
from app.api_test.models.task import ApiTask
from app.api_test.forms.task import RunTaskForm, AddTaskForm, EditTaskForm, HasTaskIdForm, DeleteTaskIdForm, \
    GetTaskListForm

ns = api_test.namespace("task", description="定时任务管理相关接口")


@ns.route('/run/')
class ApiRunTaskView(LoginRequiredView):
    def post(self):
        """ 运行定时任务 """
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
                    env=form.env.data or task.env
                ).run_case
            ).start()
            return app.restful.success(msg='触发执行成功，请等待执行完毕', data={'report_id': report.id})
        return app.restful.fail(form.get_error())


@ns.route('/list/')
class ApiTaskListView(LoginRequiredView):
    def get(self):
        """ 任务列表 """
        form = GetTaskListForm()
        if form.validate():
            return app.restful.success(data=ApiTask.make_pagination(form))
        return app.restful.fail(form.get_error())


@ns.route('/sort/')
class ApiChangeTaskSortView(LoginRequiredView):
    def put(self):
        """ 更新定时任务的排序 """
        ApiTask.change_sort(request.json.get('List'), request.json.get('pageNum'), request.json.get('pageSize'))
        return app.restful.success(msg='修改排序成功')


@ns.route('/copy/')
class ApiCopyTaskView(LoginRequiredView):
    def post(self):
        """ 复制定时任务 """
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
            return app.restful.success(msg='复制成功', data=new_task.to_dict())
        return app.restful.fail(form.get_error())


@ns.route('/')
class ApiTaskView(LoginRequiredView):

    def get(self):
        """ 获取定时任务 """
        form = HasTaskIdForm()
        if form.validate():
            return app.restful.success(data=form.task.to_dict())
        return app.restful.fail(form.get_error())

    def post(self):
        """ 新增定时任务 """
        form = AddTaskForm()
        if form.validate():
            form.num.data = ApiTask.get_insert_num(project_id=form.project_id.data)
            new_task = ApiTask().create(form.data)
            return app.restful.success(f'任务【{form.name.data}】新建成功', new_task.to_dict())
        return app.restful.fail(form.get_error())

    def put(self):
        """ 修改定时任务 """
        form = EditTaskForm()
        if form.validate():
            form.num.data = ApiTask.get_insert_num(project_id=form.project_id.data)
            form.task.update(form.data)
            return app.restful.success(f'任务【{form.name.data}】修改成功', form.task.to_dict())
        return app.restful.fail(form.get_error())

    def delete(self):
        """ 删除定时任务 """
        form = DeleteTaskIdForm()
        if form.validate():
            form.task.delete()
            return app.restful.success(f'任务【{form.task.name}】删除成功')
        return app.restful.fail(form.get_error())


@ns.route('/status/')
class ApiTaskStatusView(LoginRequiredView):
    """ 任务状态修改 """

    def post(self):
        """ 启用定时任务 """
        form = HasTaskIdForm()
        if form.validate():
            task = form.task
            try:
                res = requests.post(
                    url='http://localhost:8025/api/job/status',
                    headers=request.headers,
                    json={
                        'userId': g.user_id,
                        'task': task.to_dict(),
                        'type': 'api'
                    }
                ).json()
                if res["status"] == 200:
                    task.enable()
                    return app.restful.success(f'任务【{form.task.name}】启用成功', data=res)
                else:
                    return app.restful.fail(f'任务【{form.task.name}】启用失败', data=res)
            except Exception as error:
                return app.restful.fail(f'任务【{form.task.name}】启用失败', data=error)
        return app.restful.fail(form.get_error())

    def delete(self):
        """ 禁用定时任务 """
        form = HasTaskIdForm()
        if form.validate():
            if form.task.is_disable():
                return app.restful.fail(f'任务【{form.task.name}】的状态不为启用中')
            try:
                res = requests.delete(
                    url='http://localhost:8025/api/job/status',
                    headers=request.headers,
                    json={
                        'taskId': form.task.id,
                        'type': 'api'
                    }
                ).json()
                if res["status"] == 200:
                    form.task.disable()
                    return app.restful.success(f'任务【{form.task.name}】禁用成功', data=res)
                else:
                    return app.restful.fail(f'任务【{form.task.name}】禁用失败', data=res)
            except Exception as error:
                return app.restful.fail(f'任务【{form.task.name}】禁用失败', data=error)
        return app.restful.fail(form.get_error())
