# -*- coding: utf-8 -*-
import requests
from flask import request
from flask.views import MethodView
from flask_apscheduler import APScheduler

from config import job_server_port, main_server_host
from utils.view import restful
from utils.parse.parseCron import parse_cron
from app import create_app

job = create_app()

# 注册并启动定时任务
scheduler = APScheduler()
scheduler.init_app(job)
scheduler.start()


def login():
    response = requests.post(
        url=f'{main_server_host}/api/system/user/login',
        json={
            "account": "common",
            "password": "common"
        }
    )
    return {"X-Token": response.json()['data']['token']}


def request_run_task_api(task_id, task_type):
    """ 调执行任务接口 """
    job.logger.info(f'{"*" * 20} 开始触发执行定时任务 {"*" * 20}')

    if isinstance(task_id, str) and task_id.startswith('cron'):  # 系统定时任务
        api_addr = '/system/job/run'
    else:  # 自动化测试定时任务
        api_addr = f'/{task_type}Test/task/run'

    re = requests.post(
        url=f'{main_server_host}/api{api_addr}',
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
                func=request_run_task_api,  # 异步执行任务
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
    job.run(host='0.0.0.0', port=job_server_port)
