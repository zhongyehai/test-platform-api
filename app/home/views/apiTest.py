# -*- coding: utf-8 -*-
from flask import current_app as app

from app.home.blueprint import home
from app.api_test.models.step import ApiStep as Step
from app.baseModel import db
from app.api_test.models.project import ApiProject as Project
from app.api_test.models.module import ApiModule as Module
from app.api_test.models.api import ApiMsg as Api
from app.api_test.models.case import ApiCase as Case
from app.api_test.models.task import ApiTask as Task
from app.api_test.models.report import ApiReport as Report
from app.assist.models.hits import Hits
from utils.util.timeUtil import get_now, time_calculate, get_week_start_and_end


def get_data_by_time(model):
    """ 获取时间维度的统计 """
    last_day_add = model.query.filter(model.created_time.between(time_calculate(-1), time_calculate(0))).count()
    to_day_add = model.query.filter(model.created_time.between(time_calculate(0), get_now())).count()

    last_start_time, last_end_time = get_week_start_and_end(1)
    last_week_add = model.query.filter(model.created_time.between(last_start_time, last_end_time)).count()

    current_start_time, current_end_time = get_week_start_and_end(0)
    current_week_add = model.query.filter(model.created_time.between(current_start_time, current_end_time)).count()

    last_month_add = model.query.filter(model.created_time.between(time_calculate(-30), get_now())).count()

    return {
        "last_day_add": last_day_add,
        "to_day_add": to_day_add,
        "last_week_add": last_week_add,
        "current_week_add": current_week_add,
        "last_month_add": last_month_add,
    }


@home.login_get("/apiTest/title")
def home_get_api_test_title():
    """ 获取卡片统计 """
    return app.restful.success(
        "获取成功",
        data={
            "project": {"title": "服务数", "total": Project.query.filter().count()},
            "module": {"title": "模块数", "total": Module.query.filter().count()},
            "api": {"title": "接口数", "total": Api.query.filter().count()},
            "hit": {"title": "记录问题数", "total": Hits.query.filter().count()},
            "case": {"title": "用例数", "total": Case.query.filter().count()},
            "step": {"title": "测试步骤数", "total": Step.query.filter().count()},
            "task": {"title": "定时任务数", "total": Task.query.filter().count()},
            "report": {"title": "测试报告数", "total": Report.query.filter().count()}
        })


@home.login_get("/apiTest/project")
def home_get_api_test_project():
    """ 统计服务数 """
    time_data = get_data_by_time(Project)
    return app.restful.success(data={
        "title": "服务",
        "options": ["总数", "昨日新增", "今日新增", "本周新增", "上周新增", "30日内新增"],
        "data": [
            Project.query.filter().count(),
            time_data["last_day_add"],
            time_data["to_day_add"],
            time_data["current_week_add"],
            time_data["last_week_add"],
            time_data["last_month_add"]
        ],
    })


@home.login_get("/apiTest/module")
def home_get_api_test_module():
    """ 统计模块数 """
    time_data = get_data_by_time(Module)
    return app.restful.success(data={
        "title": "模块",
        "options": ["总数", "昨日新增", "今日新增", "本周新增", "上周新增", "30日内新增"],
        "data": [
            Module.query.filter().count(),
            time_data["last_day_add"],
            time_data["to_day_add"],
            time_data["current_week_add"],
            time_data["last_week_add"],
            time_data["last_month_add"]],
    })


@home.login_get("/apiTest/api")
def home_get_api_test_api():
    """ 统计接口数 """
    data = db.execute_query_sql("""
            select methods, count(*) as totle
                from (select case
                         when method = "GET" then "GET"
                         when method = "POST" then "POST"
                         when method = "PUT" then "PUT"
                         when method = "DELETE" then "DELETE"
                         else "Other" end as methods
                      from `api_test_api`
                     ) as t
                group by methods
            """)
    usage = db.execute_query_sql("""
            select item, count(*) as totle
                from (select IF(quote_count = 0, "not_used", "is_used") as item from `api_test_api`) as t
                group by item
        """)
    time_data = get_data_by_time(Api)
    return app.restful.success(data={
        "title": "接口",
        "options": [
            "总数",
            "GET请求", "POST请求", "PUT请求", "DELETE请求", "其他请求",
            "已使用数", "未使用数",
            "昨日新增", "今日新增", "本周新增", "上周新增", "30日内新增"
        ],
        "data": [
            sum(data.values()),
            data.get("GET", 0), data.get("POST", 0), data.get("PUT", 0), data.get("DELETE", 0),
            data.get("Other", 0),
            usage.get("is_used", 0), usage.get("not_used", 0),
            time_data["last_day_add"],
            time_data["to_day_add"],
            time_data["current_week_add"],
            time_data["last_week_add"],
            time_data["last_month_add"]
        ]
    })


@home.login_get("/apiTest/case")
def home_get_api_test_case():
    """ 统计用例数 """
    data = db.execute_query_sql("""
            select status, count(*) as totle
                from (select IF(status = 0, "not_run", "is_run") as status from `api_test_case`) as t
                group by status;
            """)
    time_data = get_data_by_time(Case)
    return app.restful.success("获取成功", data={
        "title": "用例",
        "options": [
            "总数", "要执行的用例", "不执行的用例",
            "昨日新增", "今日新增", "本周新增", "上周新增", "30日内新增"
        ],
        "data": [
            sum(data.values()),
            data.get("is_run", 0),
            data.get("not_run", 0),
            time_data["last_day_add"],
            time_data["to_day_add"],
            time_data["current_week_add"],
            time_data["last_week_add"],
            time_data["last_month_add"]
        ],
    })


@home.login_get("/apiTest/step")
def home_get_api_test_step():
    """ 统计步骤数 """
    data = db.execute_query_sql("""
            select status, count(*) as totle
                from (select IF(status = 0, "not_run", "is_run") as status from `api_test_step`) as t
                group by status;
            """)
    time_data = get_data_by_time(Step)

    return app.restful.success("获取成功", data={
        "title": "测试步骤",
        "options": [
            "总数", "要执行的步骤", "不执行的步骤",
            "昨日新增", "今日新增", "本周新增", "上周新增", "30日内新增"
        ],
        "data": [
            sum(data.values()),
            data.get("is_run", 0),
            data.get("not_run", 0),
            time_data["last_day_add"],
            time_data["to_day_add"],
            time_data["current_week_add"],
            time_data["last_week_add"],
            time_data["last_month_add"]
        ],
    })


@home.login_get("/apiTest/task")
def home_get_api_test_task():
    """ 统计定时任务数 """
    status = db.execute_query_sql("""
            select status, count(*) as totle
                from (select IF(status = 1, "enable", "disable") as status from `api_test_task` ) as t
                group by status
            """)

    time_data = get_data_by_time(Task)
    return app.restful.success("获取成功", data={
        "title": "定时任务",
        "options": [
            "总数", "启用", "禁用",
            "昨日新增", "今日新增", "本周新增", "上周新增", "30日内新增"
        ],
        "data": [
            sum(status.values()),
            status.get("enable", 0), status.get("disable", 0),
            time_data["last_day_add"],
            time_data["to_day_add"],
            time_data["current_week_add"],
            time_data["last_week_add"],
            time_data["last_month_add"]
        ]
    })


@home.login_get("/apiTest/report")
def home_get_api_test_report():
    """ 统计测试报告数 """
    is_passed = db.execute_query_sql("""
            select is_passed, count(*) as totle
                from (select IF(is_passed = 1, "is_passed", "not_passed") as is_passed from `api_test_report`) as t
                group by is_passed
            """)

    run_type = db.execute_query_sql("""
            select run_type, count(*) as totle
                from (select case 
                         when run_type = "api" then "api"
                         when run_type = "set" then "set"
                         when run_type = "case" then "case"
                         when run_type = "task" then "task" end as run_type from `api_test_report`) as t
                group by run_type
            """)
    time_data = get_data_by_time(Report)

    return app.restful.success("获取成功", data={
        "title": "测试报告",
        "options": [
            "总数", "通过数", "失败数",
            "接口生成", "用例生成", "用例集生成", "定时任务生成",
            "昨日新增", "今日新增", "本周新增", "上周新增", "30日内新增"
        ],
        "data": [
            sum(is_passed.values()),
            is_passed.get("is_passed", 0), is_passed.get("not_passed", 0),
            run_type.get("api", 0), run_type.get("case", 0), run_type.get("set", 0), run_type.get("task", 0),
            time_data["last_day_add"],
            time_data["to_day_add"],
            time_data["current_week_add"],
            time_data["last_week_add"],
            time_data["last_month_add"]
        ]
    })


@home.login_get("/apiTest/hit")
def home_get_api_test_hit():
    """ 统计命中数 """
    hit_type_data = db.execute_query_sql("""select hit_type, count(*) num from `auto_test_hits` group by hit_type""")
    time_data = get_data_by_time(Hits)

    return app.restful.success("获取成功", data={
        "title": "记录问题",
        "options": [
            "总数", *hit_type_data.keys(),
            "昨日新增", "今日新增", "本周新增", "上周新增", "30日内新增"
        ],
        "data": [
            sum(hit_type_data.values()), *hit_type_data.values(),
            time_data["last_day_add"],
            time_data["to_day_add"],
            time_data["current_week_add"],
            time_data["last_week_add"],
            time_data["last_month_add"]
        ]
    })
