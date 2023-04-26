# -*- coding: utf-8 -*-
import copy
import json

import requests
from flask import request
from flask.views import MethodView
from flask_apscheduler import APScheduler

from utils.view import restful
from utils.parse.parseCron import parse_cron
from app import create_app, db
from app.config.models.business import BusinessLine
from app.api_test.models.project import ApiProject as Project
from utils.message.sendReport import send_business_stage_count

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


def run_task_report_count(count_time="month"):
    """ 自动化测试记录阶段统计 """
    with job.app_context():
        if count_time == "week":
            count_day = 'YEARWEEK(DATE_FORMAT(created_time,"%Y-%m-%d"))=YEARWEEK(NOW())'
        elif count_time == "month":
            count_day = 'DATE_FORMAT(created_time, "%Y%m") = DATE_FORMAT(CURDATE(), "%Y%m")'

        business_list = BusinessLine.query.filter(BusinessLine.receive_type != "0").all()

        for business in business_list:
            business_template = {
                "countTime": count_time,
                "total": 0,
                "pass": 0,
                "fail": 0,
                "passRate": 0,
                "record": [],
                "hitRecord": {}
            }

            project_list = Project.get_all(business_id=business.id)
            for project in project_list:

                project_template = copy.deepcopy(business_template)
                project_template.pop("countTime")

                data_report = db.execute_query_sql(f"""SELECT
                	project_id,
                	sum( CASE is_passed WHEN 1 THEN 1 ELSE 0 END ) AS pass,
                	sum( CASE is_passed WHEN 0 THEN 1 ELSE 0 END ) AS fail 
                FROM
                	api_test_report WHERE `trigger_type` in ("cron", "pipeline") 
                    AND `status` = '2' 
                    AND `process` = '3' 
                    and project_id in ({project.id}) 
                    AND {count_day}""", False)

                data_hit = db.execute_query_sql(
                    f"""SELECT project_id,hit_type,count(hit_type)  FROM auto_test_hits 
                        WHERE project_id in ({project.id}) AND {count_day} GROUP BY hit_type """, False)

                pass_count = int(data_report[0][1]) if data_report[0][1] else 0
                fail_count = int(data_report[0][2]) if data_report[0][1] else 0
                total = pass_count + fail_count
                if total != 0:
                    project_template["name"] = project.name
                    project_template["total"] = total
                    project_template["pass"] = pass_count
                    project_template["fail"] = fail_count
                    project_template["passRate"] = round(pass_count / total, 3) if total > 0 else 0
                    project_template["hitRecord"] = {hit[1]: hit[2] for hit in data_hit}
                    project_template["record"] = []
                    business_template["record"].append(project_template)

            # 聚合业务线的数据
            business_template["webhookList"] = json.loads(business.webhook_list)
            business_template["receiveType"] = business.receive_type
            for project_count in business_template["record"]:
                business_template["total"] += project_count["total"]
                business_template["pass"] += project_count["pass"]
                business_template["fail"] += project_count["fail"]
                business_template["passRate"] += project_count["passRate"]
                for key, value in project_count["hitRecord"].items():
                    hit_record_key = business_template["hitRecord"].get(key)
                    business_template["hitRecord"][key] = hit_record_key + value if hit_record_key else value

            business_template["passRate"] = business_template["passRate"] / len(business_template["record"])
            job.logger.info(f'business_template: \n{business_template}')
            if business_template["total"] > 0:
                send_business_stage_count(business_template)


# 添加阶段统计任务
for job_data in [
    {"id": "count_of_week", "kwargs": {"count_time": "week"}, "minute": "0", "hour": "18", "day_of_week": "FRI"},
    {"id": "count_of_month", "kwargs": {"count_time": "month"}, "minute": "2", "hour": "18", "day": "last"}
]:
    if scheduler.get_job(job_data["id"]):
        scheduler.remove_job(job_data["id"])
    scheduler.add_job(
        func=run_task_report_count,
        trigger="cron",
        misfire_grace_time=60,
        coalesce=False,
        second='0',
        **job_data
    )


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
