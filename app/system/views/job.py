# -*- coding: utf-8 -*-
import copy
import json
from threading import Thread
from datetime import datetime

import requests
from flask import current_app as app, request
from app.baseModel import ApschedulerJobs, db
from app.baseView import AdminRequiredView, LoginRequiredView
from app.system.blueprint import system_manage
from app.system.models.job import JobRunLog
from app.config.models.business import BusinessLine
from app.api_test.models.project import ApiProject as Project
from utils.message.sendReport import send_business_stage_count


class JobFuncs:
    """ 定时任务，方法以cron_开头，参数放在文档注释里面 """

    @classmethod
    def cron_count_of_week(cls):
        """
        {
            "name": "周统计任务",
            "id": "cron_count_of_week",
            "cron": "0 0 18 ? * FRI"
        }
        """

        cls.run_task_report_count("cron_count_of_week", "week")

    @classmethod
    def cron_count_of_month(cls):
        """
        {
            "name": "月统计任务",
            "id": "cron_count_of_month",
            "cron": "0 1 18 last * *"
        }
        """
        cls.run_task_report_count("cron_count_of_month", "month")

    @staticmethod
    def run_task_report_count(run_func, count_time="month"):
        """ 自动化测试记录阶段统计 """

        if count_time == "week":
            count_day = 'YEARWEEK(DATE_FORMAT(created_time,"%Y-%m-%d"))=YEARWEEK(NOW())'
        elif count_time == "month":
            count_day = 'DATE_FORMAT(created_time, "%Y%m") = DATE_FORMAT(CURDATE(), "%Y%m")'

        business_list = BusinessLine.query.filter(BusinessLine.receive_type != "0").all()

        for business in business_list:
            run_log = JobRunLog().create({"business_id": business.id, "func_name": run_func})
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
                       AND project_id in ({project.id})
                       AND `process` = '3' 
                       AND `status` = '2' 
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

            if business_template["total"] > 0:
                business_template["passRate"] = business_template["passRate"] / len(business_template["record"])
                send_business_stage_count(business_template)
            run_log.run_success(business_template)


class SystemGetJobListView(AdminRequiredView):
    def get(self):
        """ 获取定时任务列表 """
        job_list = ApschedulerJobs.get_all()
        return app.restful.success("获取成功",
                                   data=[{"id": job.id, "next_run_time": job.next_run_time} for job in job_list])


class SystemGetJobFuncListView(AdminRequiredView):

    def get(self):
        """ 获取定时任务方法列表 """
        data_list = []
        for func_name in dir(JobFuncs):
            if func_name.startswith("cron_"):
                attr_doc = json.loads(getattr(JobFuncs, func_name).__doc__)
                func = {"name": attr_doc["name"], "func_name": attr_doc["id"], }
                job = ApschedulerJobs.get_first(id=f'cron_{attr_doc["id"]}')
                if job:
                    func["id"] = job.id
                    func["next_run_time"] = datetime.fromtimestamp(int(job.next_run_time)).strftime('%Y-%m-%d %H:%M:%S')
                data_list.append(func)

        return app.restful.success("获取成功", data=data_list)


class SystemRunJobView(LoginRequiredView):
    def post(self):
        """ 执行任务 """
        task_func_str = request.json.get("id")
        Thread(target=getattr(JobFuncs, task_func_str)).start()  # 异步执行，释放资源
        return app.restful.success("触发成功")


class SystemGetRunJobLogView(LoginRequiredView):
    def get(self):
        """ 执行任务记录 """
        return app.restful.success("获取成功", data=JobRunLog.make_pagination(request.args))


class SystemJobView(AdminRequiredView):
    job_host = "http://localhost:8025"

    def get(self):
        """ 获取定时任务 """
        job_id = request.args.get("id")
        return app.restful.success("获取成功", data=ApschedulerJobs.get_first(id=job_id).to_dict())

    def post(self):
        """ 新增定时任务 """
        job_func_name = request.json.get("func")
        task_conf = getattr(JobFuncs, job_func_name).__doc__
        try:
            res = requests.post(
                url="http://localhost:8025/api/job/status",
                headers=request.headers,
                json={
                    "task": json.loads(task_conf),
                    "type": "cron"
                }
            ).json()
            app.logger.info(f'添加任务【{job_func_name}】响应: \n{res}')
            return app.restful.success('操作成功')
        except:
            return app.restful.error('操作失败')

    def delete(self):
        """ 删除定时任务 """
        job_id = request.json.get("id")
        try:
            res = requests.delete(
                url="http://localhost:8025/api/job/status",
                headers=request.headers,
                json={
                    "taskId": job_id,
                    "type": "cron"
                }
            ).json()
            app.logger.info(f'删除任务【{job_id}】响应: \n{res}')
            return app.restful.success('操作成功')
        except:
            return app.restful.error('操作失败')


system_manage.add_url_rule("/job", view_func=SystemJobView.as_view("SystemJobView"))
system_manage.add_url_rule("/job/run", view_func=SystemRunJobView.as_view("SystemRunJobView"))
system_manage.add_url_rule("/job/list", view_func=SystemGetJobListView.as_view("SystemGetJobListView"))
system_manage.add_url_rule("/job/log", view_func=SystemGetRunJobLogView.as_view("SystemGetRunJobLogView"))
system_manage.add_url_rule("/job/func/list", view_func=SystemGetJobFuncListView.as_view("SystemGetJobFuncListView"))
