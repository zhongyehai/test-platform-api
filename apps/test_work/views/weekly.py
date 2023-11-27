# -*- coding: utf-8 -*-
from flask import send_from_directory, current_app as app

from ..blueprint import test_work
from ..model_factory import WeeklyConfigModel, WeeklyModel
from ..forms.weekly import GetWeeklyConfigListForm, GetWeeklyConfigForm, AddWeeklyConfigForm, ChangeWeeklyConfigForm, \
    DeleteWeeklyConfigForm, GetWeeklyListForm, GetWeeklyForm, AddWeeklyForm, ChangeWeeklyForm, DeleteWeeklyForm
from ...system.model_factory import User
from utils.util.file_util import TEMP_FILE_ADDRESS
from utils.make_data.make_weekly import make_weekly_excel, make_current_weekly_excel


@test_work.login_get("/weekly/config/list")
def test_work_get_weekly_config_list():
    """ 获取产品、项目列表 """
    form = GetWeeklyConfigListForm()
    return app.restful.get_success(WeeklyConfigModel.make_pagination(form))


@test_work.login_get("/weekly/config")
def test_work_get_weekly_config():
    """ 获取产品、项目信息 """
    form = GetWeeklyConfigForm()
    return app.restful.get_success(form.conf.to_dict())


@test_work.login_post("/weekly/config")
def test_work_add_weekly_config():
    """ 新增产品、项目 """
    form = AddWeeklyConfigForm()
    WeeklyConfigModel.model_create(form.model_dump())
    return app.restful.add_success()


@test_work.login_put("/weekly/config")
def test_work_change_weekly_config():
    """ 修改产品、项目 """
    form = ChangeWeeklyConfigForm()
    form.conf.model_update(form.model_dump())
    return app.restful.change_success()


@test_work.login_delete("/weekly/config")
def test_work_delete_weekly_config():
    """ 删除产品、项目 """
    form = DeleteWeeklyConfigForm()
    form.conf.delete()
    return app.restful.delete_success()


@test_work.login_get("/weekly/list")
def test_work_get_weekly_list():
    """ 获取周报列表 """
    form = GetWeeklyListForm()
    return app.restful.get_success(WeeklyModel.make_pagination(form))


@test_work.login_get("/weekly/download")
def test_work_download_weekly():
    """ 导出周报 """
    form = GetWeeklyListForm()
    # 获取产品、项目数据
    product_dict = WeeklyConfigModel.get_data_dict()
    user_dict = {user.id: user.name for user in User.get_all()}

    if form.download_type.data == "current":  # 导出本周周报
        data_list = WeeklyModel.make_pagination(form)
        file_name = make_current_weekly_excel(product_dict, data_list, user_dict)  # 生成excel
    else:  # 导出指定时间段的周报
        data_list = WeeklyModel.make_pagination(form)
        file_name = make_weekly_excel(data_list, form, user_dict)
    return send_from_directory(TEMP_FILE_ADDRESS, file_name, as_attachment=True)


@test_work.login_get("/weekly")
def test_work_get_weekly():
    """ 获取周报信息 """
    form = GetWeeklyForm()
    return app.restful.get_success(form.weekly.to_dict())


@test_work.login_post("/weekly")
def test_work_post_weekly():
    """ 新增周报 """
    form = AddWeeklyForm()
    WeeklyModel.model_create(form.data)
    return app.restful.add_success()


@test_work.login_put("/weekly")
def test_work_put_weekly():
    """ 修改周报 """
    form = ChangeWeeklyForm()
    form.weekly.model_update(form.model_dump())
    return app.restful.change_success()


@test_work.login_delete("/weekly")
def test_work_delete_weekly():
    """ 删除周报 """
    form = DeleteWeeklyForm()
    form.weekly.delete()
    return app.restful.delete_success()
