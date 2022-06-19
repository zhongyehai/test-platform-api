#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/11/17 15:13
# @Author : ZhongYeHai
# @Site : 
# @File : job.py
# @Software: PyCharm
import os
import json
import traceback
from threading import Thread

import requests
from flask import request
from flask.views import MethodView
from flask_apscheduler import APScheduler

from app.ui_test.task.models import UiTask
from app.ui_test.caseSet.models import UiCaeSet
from app.utils import restful
from app.utils.parseCron import parse_cron
from app.api_test.sets.models import ApiSet, db
from app.api_test.task.models import ApiTask
from app.ucenter.user.models import User
from app import create_app
from app.utils.runApiTest.runHttpRunner import RunCase as RunApiCase
from app.utils.runUiTest.runUiTestRunner import RunCase as RunUiCase
from config.config import conf

os.environ['TZ'] = 'Asia/Shanghai'

job = create_app()

# 注册并启动定时任务
scheduler = APScheduler()
scheduler.init_app(job)
scheduler.start()


def aps_test(case_ids, task, user_id=None, task_type='api'):
    """ 运行定时任务, 并发送测试报告 """
    user = User.get_first(id=user_id)
    run_fun = RunApiCase if task_type == 'api' else RunUiCase
    runner = run_fun(
        project_id=task.project_id,
        run_name=task.name,
        case_id=case_ids,
        task=task.to_dict(),
        performer=user.name,
        create_user=user.id,
        is_async=task.is_async
    )
    runner.run_case()


def async_run_test(*args):
    """ 多线程执行定时任务 """
    Thread(target=aps_test, args=args).start()


class JobStatus(MethodView):
    """ 任务状态修改 """

    def post(self):
        """ 添加定时任务 """
        user_id, task_id, task_type = request.json.get('userId'), request.json.get('taskId'), request.json.get('type')
        if task_type == 'api':
            task = ApiTask.get_first(id=task_id)
            cases_id = ApiSet.get_case_id(task.project_id, json.loads(task.set_id), json.loads(task.case_id))
        elif task_type == 'ui':
            task = UiTask.get_first(id=task_id)
            cases_id = UiCaeSet.get_case_id(task.project_id, json.loads(task.set_id), json.loads(task.case_id))
        try:
            # 把定时任务添加到apscheduler_jobs表中
            scheduler.add_job(func=async_run_test,  # 异步执行任务
                              trigger='cron',
                              misfire_grace_time=60,
                              coalesce=False,
                              args=[cases_id, task, user_id, task_type],
                              id=f'{task_type}_{str(task.id)}',
                              **parse_cron(task.cron))
            task.status = '启用中'
            db.session.commit()
            return restful.success(f'定时任务 {task.name} 启动成功')
        except Exception as error:
            return restful.error(f'定时任务启动失败', data=error)

    def delete(self):
        """ 删除定时任务 """
        task_type = request.json.get('type')
        task = ApiTask.get_first(id=request.json.get('taskId')) if task_type == 'api' else UiTask.get_first(id=request.json.get('taskId'))
        with db.auto_commit():
            task.status = '禁用中'
            scheduler.remove_job(f'{task_type}_{str(task.id)}')  # 移除任务
        return restful.success(f'任务 {task.name} 禁用成功')


job.add_url_rule('/api/job/status', view_func=JobStatus.as_view('jobStatus'))


@job.errorhandler(404)
def page_not_found(e):
    """ 捕获404的所有异常 """
    return restful.url_not_find(msg=f'接口 {request.path} 不存在')


@job.errorhandler(Exception)
def error_handler(e):
    """ 捕获所有服务器内部的异常，把错误发送到 即时达推送 的 系统错误 通道 """
    error = traceback.format_exc()
    try:
        requests.post(
            url=conf['error_push']['url'],
            json={
                'key': conf['error_push']['key'],
                'head': f'{conf["SECRET_KEY"]}报错了',
                'body': f'{error}'
            }
        )
    except:
        pass
    return restful.error(f'服务器异常: {e}')


if __name__ == '__main__':
    job.run(host='0.0.0.0', port=8025)
