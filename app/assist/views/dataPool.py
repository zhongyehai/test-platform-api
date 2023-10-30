# -*- coding: utf-8 -*-
from flask import current_app as app, request
from app.assist.blueprint import assist
from app.assist.forms.dataPool import GetDataPoolForm, PutDataPoolForm, DeleteDataPoolForm, PostDataPoolForm
from app.assist.models.dataPool import AutoTestUser, DataPool


@assist.get("/autoTestUser")
def assist_get_auto_test_user_list():
    """ 获取自动化测试用户数据列表 """
    user_list = AutoTestUser.get_all(env=request.args.get("env"))
    return app.restful.success("获取成功", data=[
        auto_user.to_dict(pop_list=["created_time", "update_time"]) for auto_user in user_list
    ])


@assist.login_get("/dataPool/list")
def assist_get_data_pool_list():
    """ 获取数据池列表 """
    form = GetDataPoolForm().do_validate()
    return app.restful.success("获取成功", DataPool.make_pagination(form))


@assist.login_get("/dataPool/businessStatus")
def assist_get_data_pool_business_status_list():
    """ 获取数据池业务状态 """
    data_list = DataPool.query.with_entities(DataPool.business_status).distinct().all()
    return app.restful.success("获取成功", [data[0] for data in data_list])


@assist.login_get("/dataPool/useStatus")
def assist_get_data_pool_use_status_list():
    """ 获取数据池使用状态 """
    return app.restful.success("获取成功", {"not_used": "未使用", "in_use": "使用中", "used": "已使用"})


@assist.login_get("/dataPool")
def assist_get_data_pool():
    """ 获取数据池数据 """
    return app.restful.success("获取成功", DataPool.get_first(id=request.args.get("id")).to_dict())


@assist.login_post("/dataPool")
def assist_add_data_pool():
    """ 新增数据池数据 """
    form = PostDataPoolForm().do_validate()
    data_pool = DataPool().create(form.data)
    return app.restful.success("新增成功", data_pool.to_dict())


@assist.login_put("/dataPool")
def assist_change_data_pool():
    """ 修改数据池数据 """
    form = PutDataPoolForm().do_validate()
    form.data_pool.update(form.data)
    return app.restful.success("修改成功", form.data_pool.to_dict())


@assist.login_delete("/dataPool")
def assist_delete_data_pool():
    """ 删除数据池数据 """
    form = DeleteDataPoolForm().do_validate()
    form.data_pool.delete()
    return app.restful.success("删除成功")
 