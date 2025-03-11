# -*- coding: utf-8 -*-
from flask import current_app as app
from sqlalchemy import func, case

from ..blueprint import api_test
from ...api_test.model_factory import ApiProject as Project, ApiModule as Module, ApiMsg as Api, ApiCase as Case, \
    ApiTask as Task, ApiReport as Report, ApiStep as Step
from ...assist.models.hits import Hits
from ...enums import DataStatusEnum
from utils.util.time_util import get_now, time_calculate, get_week_start_and_end


def get_data_by_time(model):
    """ 获取时间维度的统计 """
    last_day_add = model.query.filter(model.create_time.between(time_calculate(-1), time_calculate(0))).count()
    to_day_add = model.query.filter(model.create_time.between(time_calculate(0), get_now())).count()

    last_start_time, last_end_time = get_week_start_and_end(1)
    last_week_add = model.query.filter(model.create_time.between(last_start_time, last_end_time)).count()

    current_start_time, current_end_time = get_week_start_and_end(0)
    current_week_add = model.query.filter(model.create_time.between(current_start_time, current_end_time)).count()

    last_month_add = model.query.filter(model.create_time.between(time_calculate(-30), get_now())).count()

    return {
        "last_day_add": last_day_add,
        "to_day_add": to_day_add,
        "last_week_add": last_week_add,
        "current_week_add": current_week_add,
        "last_month_add": last_month_add,
    }


@api_test.login_get("/dashboard-card")
def get_api_test_card():
    """ 获取卡片统计 """
    return app.restful.get_success([
        {"name": "report", "title": "测试报告数", "total": Report.query.filter().count()},
        {"name": "api", "title": "接口数", "total": Api.query.filter().count()},
        {"name": "case", "title": "用例数", "total": Case.query.filter().count()},
        {"name": "step", "title": "测试步骤数", "total": Step.query.filter().count()}
    ])


@api_test.login_get("/dashboard-project")
def get_api_test_project():
    """ 统计服务数 """
    time_data = get_data_by_time(Project)
    return app.restful.get_success({
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


@api_test.login_get("/dashboard-module")
def get_api_test_module():
    """ 统计模块数 """
    time_data = get_data_by_time(Module)
    return app.restful.get_success({
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


@api_test.login_get("/dashboard-api")
def get_api_test_api():
    """ 统计接口数 """
    # 请求方法维度
    method_query = Api.db.session.query(
        func.count(),
        func.count(case(
            (Api.method == 'GET', 'GET'),
            (Api.method == 'POST', 'POST'),
            (Api.method == 'PUT', 'PUT'),
            (Api.method == 'DELETE', 'DELETE'),
            else_='Other'))
    ).filter().group_by(Api.method).all()  # [(60, 0.0), (232, 0.0), (11, 0.0), (25, 0.0), (4, 0.0), (4, 0.0), (6, 0.0)]
    method_count = [res[0] for res in method_query]  # [60, 232, 11, 25, 4, 4, 6]
    method_count.extend([0, 0, 0, 0])

    # 是否使用维度
    use_query = Api.db.session.query(
        func.count(Api.id),  # 总数
        func.sum(case((Api.use_count == DataStatusEnum.DISABLE.value, 1), else_=0)),  # 未使用
        func.sum(case((Api.use_count != DataStatusEnum.DISABLE.value, 1), else_=0))  # 已使用
    ).one()
    use_count = [int(count) if count is not None else 0 for count in use_query]
    use_count.extend([0, 0, 0, 0])

    time_data = get_data_by_time(Api)
    return app.restful.get_success({
        "title": "接口",
        "options": [
            "总数",
            "GET请求", "POST请求", "PUT请求", "DELETE请求", "其他请求",
            "未使用数", "已使用数",
            "昨日新增", "今日新增", "本周新增", "上周新增", "30日内新增"
        ],
        "data": [
            sum(method_count),
            method_count[0], method_count[1], method_count[2], method_count[3], sum(method_count[4:]),
            use_count[1], use_count[2],
            time_data["last_day_add"],
            time_data["to_day_add"],
            time_data["current_week_add"],
            time_data["last_week_add"],
            time_data["last_month_add"]
        ]
    })


@api_test.login_get("/dashboard-case")
def get_api_test_case():
    """ 统计用例数 """
    case_query = Case.db.session.query(
        func.count(Case.id),  # 总数
        func.sum(case((Case.status == DataStatusEnum.DISABLE.value, 1), else_=0)),
        func.sum(case((Case.status != DataStatusEnum.DISABLE.value, 1), else_=0))
    ).one()
    case_count = [int(count) if count is not None else 0 for count in case_query]

    time_data = get_data_by_time(Case)
    return app.restful.get_success({
        "title": "用例",
        "options": [
            "总数", "不执行的用例", "要执行的用例",
            "昨日新增", "今日新增", "本周新增", "上周新增", "30日内新增"
        ],
        "data": [
            *case_count,
            time_data["last_day_add"],
            time_data["to_day_add"],
            time_data["current_week_add"],
            time_data["last_week_add"],
            time_data["last_month_add"]
        ],
    })


@api_test.login_get("/dashboard-step")
def get_api_test_step():
    """ 统计步骤数 """
    step_query = Step.db.session.query(
        func.count(Step.id),  # 总数
        func.sum(case((Step.status == DataStatusEnum.DISABLE.value, 1), else_=0)),
        func.sum(case((Step.status != DataStatusEnum.DISABLE.value, 1), else_=0))
    ).one()
    step_count = [int(count) if count is not None else 0 for count in step_query]

    time_data = get_data_by_time(Step)

    return app.restful.get_success({
        "title": "测试步骤",
        "options": [
            "总数", "不执行的步骤", "要执行的步骤",
            "昨日新增", "今日新增", "本周新增", "上周新增", "30日内新增"
        ],
        "data": [
            *step_count,
            time_data["last_day_add"],
            time_data["to_day_add"],
            time_data["current_week_add"],
            time_data["last_week_add"],
            time_data["last_month_add"]
        ],
    })


@api_test.login_get("/dashboard-task")
def get_api_test_task():
    """ 统计定时任务数 """
    task_query = Task.db.session.query(
        func.count(Task.id),  # 总数
        func.sum(case((Task.status == DataStatusEnum.DISABLE.value, 1), else_=0)),
        func.sum(case((Task.status != DataStatusEnum.DISABLE.value, 1), else_=0))
    ).one()
    task_count = [int(count) if count is not None else 0 for count in task_query]

    time_data = get_data_by_time(Task)
    return app.restful.get_success({
        "title": "定时任务",
        "options": [
            "总数", "禁用", "启用",
            "昨日新增", "今日新增", "本周新增", "上周新增", "30日内新增"
        ],
        "data": [
            *task_count,
            time_data["last_day_add"],
            time_data["to_day_add"],
            time_data["current_week_add"],
            time_data["last_week_add"],
            time_data["last_month_add"]
        ]
    })


@api_test.login_get("/dashboard-report")
def get_api_test_report():
    """ 统计测试报告数 """
    report_query = Report.db.session.query(
        func.count(Report.id),  # 总数
        func.sum(case((Report.is_passed == DataStatusEnum.ENABLE.value, 1), else_=0)),
        func.sum(case((Report.is_passed != DataStatusEnum.ENABLE.value, 1), else_=0))
    ).one()
    report_count = [int(count) if count is not None else 0 for count in report_query]

    run_type_query = Report.db.session.query(
        func.count(),
        func.count(case(
            (Report.run_type == 'api', 'api'),
            (Report.run_type == 'case', 'case'),
            (Report.run_type == 'suite', 'suite'),
            (Report.run_type == 'task', 'task'),
            else_='Other'))
    ).filter().group_by(Report.run_type).all()  # [(465, 465), (2612, 2612), (15, 15), (5, 5)]
    run_type_count = [res[0] for res in run_type_query]  # [465, 2612, 15, 5]

    time_data = get_data_by_time(Report)

    return app.restful.get_success({
        "title": "测试报告",
        "options": [
            "总数", "通过数", "失败数",
            "定时任务生成", "用例生成", "接口生成",
            "昨日新增", "今日新增", "本周新增", "上周新增", "30日内新增"
        ],
        "data": [
            *report_count, *run_type_count,
            time_data["last_day_add"],
            time_data["to_day_add"],
            time_data["current_week_add"],
            time_data["last_week_add"],
            time_data["last_month_add"]
        ]
    })


@api_test.login_get("/dashboard-hit")
def get_api_test_hit():
    """ 统计命中数 """
    hit_type_data = Hits.db.execute_query_sql(
        f"""select hit_type, count(*) num from `{Hits.__tablename__}` group by hit_type""")
    time_data = get_data_by_time(Hits)

    return app.restful.get_success({
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
