# -*- coding: utf-8 -*-
import requests
from flask import request
from flask.views import MethodView
from flask_apscheduler import APScheduler

from utils.view import restful
from utils.parse.parseCron import parse_cron
from app import create_app

job = create_app()

# 注册并启动定时任务
scheduler = APScheduler()
scheduler.init_app(job)
scheduler.start()

host = "http://localhost:8024"


def login():
    response = requests.post(
        url=f'{host}/api/system/user/login',
        json={
            "account": "common",
            "password": "common"
        }
    )
    return {"X-Token": response.json()['data']['token']}


def run_task(task_id, task_type):
    job.logger.info(f'{"*" * 20} 开始触发执行定时任务 {"*" * 20}')
    re = requests.post(
        url=f'{host}/api/{task_type}Test/task/run',
        headers=login(),
        json={
            "id": task_id,
            "trigger_type": "cron"
        }
    )
    job.logger.info(f'{"*" * 20} 定时任务触发完毕 {"*" * 20}')
    job.logger.info(f'{"*" * 20} 触发响应为：{re.json()} {"*" * 20}')


class JobStatus(MethodView):
    """ 任务状态修改 """

    def post(self):
        """ 添加定时任务 """
        user_id, task, task_type = request.json.get('userId'), request.json.get('task'), request.json.get('type')

        with job.db.auto_commit():
            scheduler.add_job(
                func=run_task,  # 异步执行任务
                trigger="cron",
                misfire_grace_time=60,
                coalesce=False,
                kwargs={"task_id": task["id"], "task_type": task_type},
                id=f'{task_type}_{str(task["id"])}',
                **parse_cron(task["cron"])
            )
        return restful.success(f'定时任务启动成功')

    def delete(self):
        """ 删除定时任务 """
        task_type, task_id = request.json.get('type'), request.json.get('taskId')
        with job.db.auto_commit():
            scheduler.remove_job(f'{task_type}_{str(task_id)}')  # 移除任务
        return restful.success(f'任务禁用成功')


job.add_url_rule('/api/job/status', view_func=JobStatus.as_view('jobStatus'))

if __name__ == '__main__':
    job.run(host='0.0.0.0', port=8025)
