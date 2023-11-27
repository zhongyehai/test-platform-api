# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import assist
from ..forms.data_pool import GetDataPoolForm, PutDataPoolForm, DeleteDataPoolForm, PostDataPoolForm, \
    GetDataPoolListForm, GetAutoTestUserDataListForm
from ..model_factory import AutoTestUser, DataPool


@assist.get("/autoTestUser")
def assist_get_auto_test_user_list():
    """ 获取自动化测试用户数据列表 """
    form = GetAutoTestUserDataListForm()
    get_filed = [AutoTestUser.id, AutoTestUser.mobile,  AutoTestUser.password,  AutoTestUser.access_token,
                 AutoTestUser.refresh_token,  AutoTestUser.company_name,  AutoTestUser.role,  AutoTestUser.env]
    return app.restful.get_success(AutoTestUser.make_pagination(form, get_filed=get_filed))


@assist.login_get("/dataPool/list")
def assist_get_data_pool_list():
    """ 获取数据池列表 """
    form = GetDataPoolListForm()
    return app.restful.get_success(DataPool.make_pagination(form))


@assist.login_get("/dataPool/businessStatus")
def assist_get_data_pool_business_status_list():
    """ 获取数据池业务状态 """
    data_list = DataPool.query.with_entities(DataPool.business_status).distinct().all()
    return app.restful.get_success([data[0] for data in data_list])


@assist.login_get("/dataPool/useStatus")
def assist_get_data_pool_use_status_list():
    """ 获取数据池使用状态 """
    return app.restful.get_success({"not_used": "未使用", "in_use": "使用中", "used": "已使用"})


@assist.login_get("/dataPool")
def assist_get_data_pool():
    """ 获取数据池数据 """
    form = GetDataPoolForm()
    return app.restful.get_success(form.data_pool.to_dict())


@assist.login_post("/dataPool")
def assist_add_data_pool():
    """ 新增数据池数据 """
    form = PostDataPoolForm()
    DataPool.model_create(form.model_dump())
    return app.restful.add_success()


@assist.login_put("/dataPool")
def assist_change_data_pool():
    """ 修改数据池数据 """
    form = PutDataPoolForm()
    form.data_pool.model_update(form.model_dump())
    return app.restful.change_success()


@assist.login_delete("/dataPool")
def assist_delete_data_pool():
    """ 删除数据池数据 """
    form = DeleteDataPoolForm()
    form.data_pool.delete()
    return app.restful.delete_success()
