# -*- coding: utf-8 -*-
from flask import current_app as app, request
from sqlalchemy import func

from ..forms.stat import AnalyseForm
from ..blueprint import api_test
from apps.config.model_factory import BusinessLine
from apps.api_test.model_factory import ApiProject as Project, ApiReport as Report
from apps.system.model_factory import User
from utils.util.time_util import time_calculate, get_now


def get_use_stat(time_off_set, project_list: list = [], get_card=False):
    """ 获取时间段的统计 """
    page_trigger_count, page_trigger_pass_count, page_trigger_pass_rate = 0, 0, 0  # 页面触发使用次数维度
    patrol_count, patrol_pass_count, patrol_pass_rate = 0, 0, 0  # 巡检维度

    start_time, end_time = time_calculate(time_off_set), get_now()
    time_slot = Report.create_time.between(start_time, end_time)
    is_passed = Report.is_passed == 1
    if get_card is True:
        # 人工使用（页面触发）统计
        run_type = Report.trigger_type == "page"
        page_trigger_count = Report.query.filter(time_slot, run_type).count()
        if page_trigger_count > 0:
            page_trigger_pass_count = Report.query.filter(time_slot, run_type, is_passed).count()
            page_trigger_pass_rate = round(page_trigger_pass_count / page_trigger_count, 4)

        # cron巡检统计
        run_type = Report.trigger_type == "cron"
        patrol_count = Report.query.filter(time_slot, run_type).count()
        if patrol_count > 0:
            patrol_pass_count = Report.query.filter(time_slot, is_passed, run_type).count()
            patrol_pass_rate = round(patrol_pass_count / patrol_count, 4)
    else:
        if project_list:
            project_id_in = Report.project_id.in_(project_list)

            # 人工使用（页面触发）统计
            run_type = Report.trigger_type == "page"
            page_trigger_count = Report.query.filter(time_slot, project_id_in, run_type).count()
            if page_trigger_count > 0:
                page_trigger_pass_count = Report.query.filter(time_slot, run_type, is_passed, project_id_in).count()
                page_trigger_pass_rate = round(page_trigger_pass_count / page_trigger_count, 4)

            # cron巡检统计
            run_type = Report.trigger_type == "cron"
            patrol_count = Report.query.filter(time_slot, run_type, project_id_in).count()
            if patrol_count > 0:
                patrol_pass_count = Report.query.filter(time_slot, is_passed, run_type, project_id_in).count()
                patrol_pass_rate = round(patrol_pass_count / patrol_count, 4)

            # # 造数据统计
            # if not project_list:
            #     project_query_set = Project.query.with_entities(Project.id).filter().all()
            #     project_list = [query_set[0] for query_set in project_query_set]
            #
            # make_data_count = Report.db.session.query(ReportCase.report_id).filter(Suite.project_id.in_(project_list)).filter(
            #     Suite.suite_type == 'assist').filter(Case.suite_id == Suite.id).filter(ReportCase.from_id == Case.id).filter(
            #     ReportCase.create_time.between(start_time, end_time)).distinct().count()

    return {
        "page_trigger_count": page_trigger_count,
        "page_trigger_pass_count": page_trigger_pass_count,
        "page_trigger_pass_rate": page_trigger_pass_rate,
        "patrol_count": patrol_count,
        "patrol_pass_count": patrol_pass_count,
        "patrol_pass_rate": patrol_pass_rate,
        # "make_data_count": make_data_count
    }


@api_test.login_get("/stat/use/card")
def api_get_stat_use_card():
    """ 使用统计卡片 """
    use_stat = get_use_stat(request.args.get("time_slot"), get_card=True)
    return app.restful.get_success(use_stat)


@api_test.login_get("/stat/use/chart")
def api_get_stat_use_chart():
    """ 使用统计图表 """
    options_list = []
    page_trigger_count_list, page_trigger_pass_count_list, page_trigger_pass_rate_list = [], [], []  # 页面使用维度
    patrol_count_list, patrol_pass_count_list, patrol_pass_rate_list = [], [], []  # 巡检维度
    # make_data_count_list = []  # 造数据维度

    business_query_set = (
        BusinessLine.query.with_entities(BusinessLine.id, BusinessLine.name).filter().all())  # [(1, '公共业务线')]
    for business_line in business_query_set:
        options_list.append(business_line[1])
        project_query_set = Project.query.with_entities(Project.id).filter(
            Project.business_id == business_line[0]).all()  # [(1,)]
        project_list = [query_set[0] for query_set in project_query_set]
        business_stat = get_use_stat(request.args.get("time_slot"), project_list)

        page_trigger_count_list.append(business_stat.get("page_trigger_count", 0))
        page_trigger_pass_count_list.append(business_stat.get("page_trigger_pass_count", 0))
        page_trigger_pass_rate_list.append(business_stat.get("page_trigger_pass_rate", 0))
        patrol_count_list.append(business_stat.get("patrol_count", 0))
        patrol_pass_count_list.append(business_stat.get("patrol_pass_count", 0))
        patrol_pass_rate_list.append(business_stat.get("patrol_pass_rate", 0))
        # make_data_count_list.append(business_stat.get("make_data_count", 0))

    return app.restful.get_success({
        "options_list": options_list,
        "items": [
            {"name": "人工触发次数", "type": "bar", "data": page_trigger_count_list},
            {"name": "人工通过次数", "type": "bar", "data": page_trigger_pass_count_list},
            {"name": "巡检次数", "type": "bar", "data": patrol_count_list},
            {"name": "巡检通过次数", "type": "bar", "data": patrol_pass_count_list}
        ]
    })


@api_test.login_get("/stat/analyse")
def api_get_analyse():
    """ 使用分析饼图 """

    form = AnalyseForm()
    filters = form.get_query_filter()

    # 执行次数维度统计
    all_count = Report.query.filter(*filters).count()
    pass_count = Report.query.filter(*filters, Report.is_passed == 1).count()
    fail_count = all_count - pass_count

    # 创建人执行次数统计
    create_user_count = Report.db.session.query(
        User.name, func.count(User.id)).filter(
        *filters, User.id == Report.create_user).group_by(Report.create_user).all()
    return app.restful.success("获取成功", data={
        "use_count": {
            "stat": {
                "title": "执行次数统计",
                "stat_list": [
                    {"name": "通过数量", "value": pass_count},
                    {"name": "不通过数量", "value": fail_count},
                ]
            },
            "detail": {"all_count": all_count, "pass_count": pass_count, "fail_count": fail_count}
        },
        "create": {
            "stat": {
                "title": "执行人员统计",
                "stat_list": [{"name": data[0], "value": data[1]} for data in create_user_count]
            }
        }
    })
