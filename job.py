# -*- coding: utf-8 -*-

import json
from threading import Thread

from flask import request
from flask.views import MethodView
from flask_apscheduler import APScheduler

from app.ui_test.models.task import UiTask
from app.ui_test.models.caseSet import UiCaeSet
from utils import restful
from utils.parseCron import parse_cron
from app.api_test.models.caseSet import ApiSet, db
from app.api_test.models.task import ApiTask
from app.ucenter.models.user import User
from app import create_app
from utils.client.runApiTest.runHttpRunner import RunCase as RunApiCase
from utils.client.runUiTest.runUiTestRunner import RunCase as RunUiCase

job = create_app()

# 注册并启动定时任务
scheduler = APScheduler()
scheduler.init_app(job)
scheduler.start()


def async_run_test(case_ids, task, user_id=None, task_type='api'):
    """ 运行定时任务, 并发送测试报告 """
    user = User.get_first(id=user_id)
    run_fun = RunApiCase if task_type == 'api' else RunUiCase
    Thread(
        target=run_fun(
            project_id=task.project_id,
            run_name=task.name,
            case_id=case_ids,
            task=task.to_dict(),
            performer=user.name,
            create_user=user.id,
            is_async=task.is_async,
            env=task.env,
            is_rollback=True
        ).run_case
    ).start()


class JobStatus(MethodView):
    """ 任务状态修改 """

    def post(self):
        """ 添加定时任务 """
        user_id, task_id, task_type = request.json.get('userId'), request.json.get('taskId'), request.json.get('type')
        task_model, case_set_model = (ApiTask, ApiSet) if task_type == 'api' else (UiTask, UiCaeSet)

        task = task_model.get_first(id=task_id)
        cases_id = case_set_model.get_case_id(task.project_id, json.loads(task.set_ids), json.loads(task.case_ids))
        with db.auto_commit():
            scheduler.add_job(
                func=async_run_test,  # 异步执行任务
                trigger='cron',
                misfire_grace_time=60,
                coalesce=False,
                kwargs={"case_ids": cases_id, "task": task, "user_id": user_id, "task_type": task_type},
                id=f'{task_type}_{str(task.id)}',
                **parse_cron(task.cron)
            )
            task.status = 1
        return restful.success(f'定时任务 {task.name} 启动成功')

    def delete(self):
        """ 删除定时任务 """
        task_type, task_id = request.json.get('type'), request.json.get('taskId')
        task = ApiTask.get_first(id=task_id) if task_type == 'api' else UiTask.get_first(id=task_id)
        with db.auto_commit():
            task.status = 0
            scheduler.remove_job(f'{task_type}_{str(task.id)}')  # 移除任务
        return restful.success(f'任务 {task.name} 禁用成功')


job.add_url_rule('/api/job/status', view_func=JobStatus.as_view('jobStatus'))

if __name__ == '__main__':
    job.run(host='0.0.0.0', port=8025)
