# -*- coding: utf-8 -*-
import copy
import json
from threading import Thread
from datetime import datetime

import requests
from flask import current_app as app, request

from ..forms.job import GetJobRunLogList, GetJobForm, GetJobLogForm, EnableJobForm, DisableJobForm, RunJobForm
from ..model_factory import ApschedulerJobs
from ..blueprint import system_manage
from ..model_factory import JobRunLog
from ...config.model_factory import BusinessLine
from ...api_test.model_factory import ApiProject, ApiReport, ApiReportCase, ApiReportStep, ApiCase, ApiStep, \
    ApiMsg, ApiProjectEnv
from ...ui_test.model_factory import WebUiReport, WebUiReportCase, WebUiReportStep, WebUiCase, WebUiStep, \
    WebUiProjectEnv, WebUiProject
from ...app_test.model_factory import AppUiReport, AppUiReportCase, AppUiReportStep, AppUiCase, AppUiStep, \
    AppUiProjectEnv, AppUiProject
from utils.message.send_report import send_business_stage_count
from config import _job_server_host
from ... import create_app


class JobFuncs:
    """ 定时任务，方法以cron_开头，参数放在文档注释里面 """

    @classmethod
    def cron_clear_report(cls):
        """
        {
            "name": "清理测试报告不存在的报告数据",
            "id": "cron_clear_report",
            "cron": "0 0 2 * * ?"
        }
        """
        with create_app().app_context():
            ApiReport.batch_delete_report_detail_data(ApiReportCase, ApiReportStep)
            WebUiReport.batch_delete_report_detail_data(WebUiReportCase, WebUiReportStep)
            AppUiReport.batch_delete_report_detail_data(AppUiReportCase, AppUiReportStep)

    @classmethod
    def cron_clear_step(cls):
        """
        {
            "name": "清理用例不存在的步骤",
            "id": "cron_clear_step",
            "cron": "0 10 2 * * ?"
        }
        """
        with create_app().app_context():
            ApiCase.batch_delete_step(ApiStep)
            WebUiCase.batch_delete_step(WebUiStep)
            AppUiCase.batch_delete_step(AppUiStep)

    @classmethod
    def cron_api_use_count(cls):
        """
        {
            "name": "统计接口使用情况",
            "id": "cron_api_use_count",
            "cron": "0 15 2,13 * * ?"
        }
        """
        with create_app().app_context():
            api_id_list = ApiMsg.get_id_list()
            for api_id in api_id_list:
                use_count = ApiStep.query.filter_by(api_id=api_id).count()
                ApiMsg.query.filter_by(id=api_id).update({"use_count": use_count})

    @classmethod
    def cron_clear_project_env(cls):
        """
        {
            "name": "清理服务不存在的服务环境数据",
            "id": "cron_clear_project_env",
            "cron": "0 20 2 * * ?"
        }
        """
        with create_app().app_context():
            ApiProject.clear_env(ApiProjectEnv)
            WebUiProject.clear_env(WebUiProjectEnv)
            AppUiProject.clear_env(AppUiProjectEnv)

    @classmethod
    def cron_count_of_week(cls):
        """
        {
            "name": "周统计任务",
            "id": "cron_count_of_week",
            "cron": "0 0 18 ? * FRI"
        }
        """
        with create_app().app_context():
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
        with create_app().app_context():
            cls.run_task_report_count("cron_count_of_month", "month")

    @staticmethod
    def run_task_report_count(run_func, count_time="month"):
        """ 自动化测试记录阶段统计 """

        if count_time == "week":
            count_day = 'YEARWEEK(DATE_FORMAT(create_time,"%Y-%m-%d"))=YEARWEEK(NOW())'
        elif count_time == "month":
            count_day = 'DATE_FORMAT(create_time, "%Y%m") = DATE_FORMAT(CURDATE(), "%Y%m")'

        with create_app().app_context():
            business_list = BusinessLine.query.filter(BusinessLine.receive_type != "0").all()

            for business in business_list:
                run_log = JobRunLog.model_create({"business_id": business.id, "func_name": run_func})
                business_template = {
                    "countTime": count_time,
                    "total": 0,
                    "pass": 0,
                    "fail": 0,
                    "passRate": 0,
                    "record": [],
                    "hitRecord": {}
                }

                project_list = ApiProject.get_all(business_id=business.id)
                for project in project_list:

                    project_template = copy.deepcopy(business_template)
                    project_template.pop("countTime")

                    data_report = ApiReport.db.execute_query_sql(f"""SELECT
                           project_id,
                           sum( CASE is_passed WHEN 1 THEN 1 ELSE 0 END ) AS pass,
                           sum( CASE is_passed WHEN 0 THEN 1 ELSE 0 END ) AS fail 
                       FROM
                           api_test_report WHERE `trigger_type` in ("cron", "pipeline") 
                           AND project_id in ({project.id})
                           AND `process` = '3' 
                           AND `status` = '2' 
                           AND {count_day}""", False)

                    data_hit = ApiReport.db.execute_query_sql(
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


@system_manage.admin_get("/job/list")
def system_manage_get_job_list():
    """ 获取定时任务列表 """
    job_query = ApschedulerJobs.db.session.query(ApschedulerJobs.id, ApschedulerJobs.next_run_time).filter().all()
    return app.restful.app.restful.get_success([{"id": job[0], "next_run_time": job[1]} for job in job_query])


@system_manage.admin_get("/job/func-list")
def system_manage_get_job_func_list():
    """ 获取定时任务方法列表 """
    data_list = []
    for func_name in dir(JobFuncs):
        if func_name.startswith("cron_"):
            attr_doc = json.loads(getattr(JobFuncs, func_name).__doc__)
            func = {"name": attr_doc["name"], "func_name": attr_doc["id"], "cron": attr_doc["cron"]}
            job_query = ApschedulerJobs.db.session.query(
                ApschedulerJobs.id, ApschedulerJobs.next_run_time
            ).filter(ApschedulerJobs.id == f'cron_{attr_doc["id"]}').first()
            # job = ApschedulerJobs.get_first(id=f'cron_{attr_doc["id"]}')
            if job_query:
                func["id"] = job_query[0]
                func["next_run_time"] = datetime.fromtimestamp(int(job_query[1])).strftime('%Y-%m-%d %H:%M:%S')
            data_list.append(func)

    return app.restful.get_success(data_list)


@system_manage.login_post("/job/run")
def system_manage_run_job():
    """ 执行任务 """
    form = RunJobForm()
    Thread(target=getattr(JobFuncs, form.func_name)).start()
    return app.restful.trigger_success()


@system_manage.admin_get("/job/log-list")
def system_manage_get_run_job_log_list():
    """ 执行任务记录列表 """
    form = GetJobRunLogList()
    get_filed = [JobRunLog.id, JobRunLog.create_time, JobRunLog.func_name, JobRunLog.business_id, JobRunLog.status]
    return app.restful.get_success(JobRunLog.make_pagination(form, get_filed=get_filed))


@system_manage.admin_get("/job/log")
def system_manage_get_run_job_log():
    """ 执行任务记录 """
    form = GetJobLogForm()
    return app.restful.get_success(form.job_log.to_dict())


@system_manage.admin_get("/job")
def system_manage_get_job():
    """ 获取定时任务 """
    form = GetJobForm()
    return app.restful.get_success(form.job.to_dict())


@system_manage.admin_post("/job")
def system_manage_enable_job():
    """ 启用定时任务 """
    form = EnableJobForm()
    task_conf = getattr(JobFuncs, form.func_name).__doc__
    try:
        res = requests.post(
            url=_job_server_host,
            headers=request.headers,
            json={
                "task": json.loads(task_conf),
                "type": "cron"
            }
        ).json()
        app.logger.info(f'添加任务【{form.func_name}】响应: \n{res}')
        return app.restful.success('操作成功')
    except:
        return app.restful.error('操作失败')


@system_manage.admin_delete("/job")
def system_manage_disable_job():
    """ 禁用定时任务 """
    form = DisableJobForm()
    try:
        res = requests.delete(
            url=_job_server_host,
            headers=request.headers,
            json={
                "task_id": form.func_name,
                "type": "cron"
            }
        ).json()
        app.logger.info(f'删除任务【{form.func_name}】响应: \n{res}')
        return app.restful.success('操作成功')
    except:
        return app.restful.error('操作失败')
