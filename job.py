# -*- coding: utf-8 -*-
import datetime

import requests
from flask import request
from flask.views import MethodView
from flask_apscheduler import APScheduler

from apps.config.model_factory import Config
from config import _job_server_port, _main_server_host
from utils.view import restful
from utils.parse.parse_cron import parse_cron
from apps import create_app

job = create_app()

# 注册并启动定时任务
scheduler = APScheduler()
scheduler.init_app(job)
scheduler.start()


def login_and_get_headers():
    response = requests.post(
        url=f'{_main_server_host}/api/system/user/login',
        json={
            "account": "common",
            "password": "common"
        }
    )
    return {"X-Token": response.json()['data']['token']}


def request_run_task_api(task_id, task_type, skip_holiday=1):
    """ 调执行任务接口 """
    job.logger.info(f'{"*" * 20} 开始触发执行定时任务 {"*" * 20}')
    if skip_holiday:
        today = datetime.datetime.now().strftime("%m-%d")
        with create_app().app_context():
            holiday_list = Config.get_first(name="holiday_list").value
        if today in holiday_list:
            job.logger.info(f'skip_holiday跳过执行')
            return

    if isinstance(task_id, str) and task_id.startswith('cron'):  # 系统定时任务
        api_addr = '/system/job/run'
    else:  # 自动化测试定时任务
        api_addr = f'/{task_type}-test/task/run'

    re = requests.post(
        url=f'{_main_server_host}/api{api_addr}',
        headers=login_and_get_headers(),
        json={
            "id": task_id,
            "func_name": task_id,
            "trigger_type": "cron"
        }
    )
    job.logger.info(f'{"*" * 20} 定时任务触发完毕 {"*" * 20}')
    job.logger.info(f'{"*" * 20} 触发响应为：{re.json()} {"*" * 20}')


class JobStatus(MethodView):
    """ 任务状态修改 """

    def post(self):
        """ 添加定时任务 """
        task, task_type = request.json.get('task'), request.json.get('type')

        with job.db.auto_commit():
            scheduler.add_job(
                func=request_run_task_api,  # 异步执行任务
                trigger="cron",
                misfire_grace_time=60,
                coalesce=False,
                kwargs={"task_id": task["id"], "task_type": task_type, "skip_holiday": task.get('skip_holiday')},
                id=f'{task_type}_{str(task["id"])}',
                **parse_cron(task["cron"])
            )
        return restful.success(f'定时任务启动成功')

    def delete(self):
        """ 删除定时任务 """
        task_type, task_id = request.json.get('type'), request.json.get('task_id')
        with job.db.auto_commit():
            scheduler.remove_job(f'{task_type}_{str(task_id)}')  # 移除任务
        return restful.success(f'任务禁用成功')


job.add_url_rule('/api/job/status', view_func=JobStatus.as_view('jobStatus'))

if __name__ == '__main__':
    job.run(host='0.0.0.0', port=_job_server_port)
