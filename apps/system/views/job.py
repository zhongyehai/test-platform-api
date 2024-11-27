# -*- coding: utf-8 -*-
import copy
import json
from threading import Thread
import datetime

import requests
from flask import current_app as app, request

from utils.util.file_util import FileUtil
from ..forms.job import GetJobRunLogList, GetJobForm, GetJobLogForm, EnableJobForm, DisableJobForm, RunJobForm
from ..model_factory import ApschedulerJobs
from ..blueprint import system_manage
from ..model_factory import JobRunLog
from ...config.model_factory import BusinessLine, WebHook
from ...api_test.model_factory import ApiProject, ApiReport, ApiReportCase, ApiReportStep, ApiCase, ApiStep, \
    ApiMsg, ApiProjectEnv, ApiCaseSuite, ApiTask
from ...enums import DataStatusEnum
from ...ui_test.model_factory import WebUiReport, WebUiReportCase, WebUiReportStep, WebUiCase, WebUiStep, \
    WebUiProjectEnv, WebUiProject, WebUiCaseSuite, WebUiTask
from ...app_test.model_factory import AppUiReport, AppUiReportCase, AppUiReportStep, AppUiCase, AppUiStep, \
    AppUiProjectEnv, AppUiProject, AppUiCaseSuite, AppUiTask
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
    def cron_clear_report_detail(cls):
        """
        {
            "name": "清理30前的报告详细数据",
            "id": "cron_clear_report_detail",
            "cron": "0 35 2 * * ?"
        }
        """
        with create_app().app_context():
            time_point = (datetime.datetime.now() - datetime.timedelta(days=30))
            # 清理测试报告数据
            ApiReportCase.query.filter(ApiReportCase.create_time < time_point).delete()
            ApiReportStep.query.filter(ApiReportStep.create_time < time_point).delete()

            # 清理测试报告截图
            report_query_set = AppUiReportCase.query.with_entities(AppUiReportCase.report_id).filter(AppUiReportCase.create_time < time_point).distinct().all()
            FileUtil.delete_report_img_by_report_id([query_set[0] for query_set in report_query_set], 'app')
            AppUiReportCase.query.filter(AppUiReportCase.create_time < time_point).delete()
            AppUiReportStep.query.filter(AppUiReportStep.create_time < time_point).delete()

            # 清理测试报告截图
            report_query_set = WebUiReportCase.query.with_entities(WebUiReportCase.report_id).filter(WebUiReportCase.create_time < time_point).distinct().all()
            FileUtil.delete_report_img_by_report_id([query_set[0] for query_set in report_query_set], 'app')
            WebUiReportCase.query.filter(WebUiReportCase.create_time < time_point).delete()
            WebUiReportStep.query.filter(WebUiReportStep.create_time < time_point).delete()

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
            run_log = JobRunLog.model_create_and_get({"business_id": -99, "func_name": "cron_api_use_count"})
            api_id_list = ApiMsg.get_id_list()
            change_dict = {}
            for api_id in api_id_list:
                use_count = ApiStep.query.filter_by(api_id=api_id, status=DataStatusEnum.ENABLE.value).count()
                db_use_count = ApiMsg.db.session.query(ApiMsg.use_count).filter(ApiMsg.id == api_id).first()[0]
                if use_count != db_use_count:
                    change_dict[
                        api_id] = f"数据库:【{db_use_count}】，实时统计:【{use_count}】, 差值:【{use_count - db_use_count}】"
                    ApiMsg.query.filter_by(id=api_id).update({"use_count": use_count})
            run_log.run_success(change_dict)

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
    def cron_clear_case_quote(cls):
        """
        {
            "name": "清理任务对于已删除的用例的引用",
            "id": "cron_clear_case_quote",
            "cron": "0 25 2 * * ?"
        }
        """
        with create_app().app_context():
            ApiTask.clear_case_quote(ApiCase, ApiCaseSuite)
            WebUiTask.clear_case_quote(WebUiCase, WebUiCaseSuite)
            AppUiTask.clear_case_quote(AppUiCase, AppUiCaseSuite)

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
            business_list = BusinessLine.query.filter(BusinessLine.receive_type != "not_receive").all()

            for business in business_list:
                run_log = JobRunLog.model_create_and_get({"business_id": business.id, "func_name": run_func})
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
                business_template["receiveType"] = business.receive_type
                business_template["webhookList"] = WebHook.get_webhook_list(business.receive_type,
                                                                            business.webhook_list)
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
    return app.restful.get_success([{"id": job[0], "next_run_time": job[1]} for job in job_query])


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
                func["next_run_time"] = datetime.datetime.fromtimestamp(int(job_query[1])).strftime('%Y-%m-%d %H:%M:%S')
            data_list.append(func)

    return app.restful.get_success(data_list)


@system_manage.post("/job/run")
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
