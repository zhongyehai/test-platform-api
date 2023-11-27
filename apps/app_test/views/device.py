# -*- coding: utf-8 -*-
import requests
from flask import current_app as app

from ..blueprint import app_test
from ...base_form import ChangeSortForm
from ..model_factory import AppUiRunServer as Server, AppUiRunPhone as Phone
from ..forms.device import (
    AddServerForm, GetServerForm, EditServerForm, GetServerListForm,
    AddPhoneForm, GetPhoneForm, EditPhoneForm, GetPhoneListForm
)


@app_test.login_get("/device/server/list")
def app_get_run_server_list():
    """ 服务器列表 """
    form = GetServerListForm()
    if form.detail:
        get_filed = [Server.id, Server.name, Server.os, Server.ip, Server.port, Server.status]
    else:
        get_filed = [Server.id, Server.name, Server.status]
    return app.restful.get_success(Server.make_pagination(form, get_filed=get_filed))


@app_test.login_put("/device/server/sort")
def app_change_server_sort():
    """ 更新服务器的排序 """
    form = ChangeSortForm()
    Server.change_sort(**form.model_dump())
    return app.restful.change_success()


@app_test.login_post("/device/server/copy")
def app_copy_server():
    """ 复制服务器 """
    form = GetServerForm()
    form.server.copy()
    return app.restful.copy_success()


@app_test.login_get("/device/server/run")
def app_run_server():
    """ 调appium服务器 """
    form = GetServerForm()
    try:
        status_code = requests.get(f'http://{form.server.ip}:{form.server.port}', timeout=5).status_code
    except Exception as error:
        form.server.request_fail()
        return app.restful.fail(msg="设置的appium服务器地址不能访问，请检查")
    if status_code > 499:  # 5开头的
        form.server.request_fail()
        return app.restful.fail(msg=f'设置的appium服务器地址响应状态码为 {status_code}，请检查')
    form.server.request_success()
    return app.restful.success(msg=f'服务器访问成功，响应为：状态码为 {status_code}')


@app_test.login_get("/device/server")
def app_get_server():
    """ 获取服务 """
    form = GetServerForm()
    return app.restful.get_success(form.server.to_dict())


@app_test.login_post("/device/server")
def app_add_server():
    """ 新增服务 """
    form = AddServerForm()
    Server.model_create(form.model_dump())
    return app.restful.add_success()


@app_test.login_put("/device/server")
def app_change_server():
    """ 修改服务 """
    form = EditServerForm()
    form.server.model_update(form.model_dump())
    return app.restful.change_success()


@app_test.login_delete("/device/server")
def app_delete_server():
    """ 删除服务 """
    form = GetServerForm()
    form.server.delete()
    return app.restful.delete_success()


@app_test.login_get("/device/phone/list")
def app_get_phone_list():
    """ 手机列表 """
    form = GetPhoneListForm()
    if form.detail:
        get_filed = [Phone.id, Phone.name, Phone.os, Phone.os_version, Phone.device_id, Phone.screen]
    else:
        get_filed = Phone.get_simple_filed_list()
    return app.restful.get_success(Phone.make_pagination(form, get_filed=get_filed))


@app_test.login_put("/device/phone/sort")
def app_change_phone_sort():
    """ 更新手机列表的排序 """
    form = ChangeSortForm()
    Phone.change_sort(**form.model_dump())
    return app.restful.change_success()


@app_test.login_post("/device/phone/copy")
def app_copy_phone():
    """ 复制手机 """
    form = GetPhoneForm()
    form.phone.copy()
    return app.restful.copy_success()


@app_test.login_get("/device/phone")
def app_get_phone():
    """ 获取手机 """
    form = GetPhoneForm()
    return app.restful.success(data=form.phone.to_dict())


@app_test.login_post("/device/phone")
def app_add_phone():
    """ 新增手机 """
    form = AddPhoneForm()
    Phone.model_create(form.model_dump())
    return app.restful.add_success()


@app_test.login_put("/device/phone")
def app_change_phone():
    """ 修改手机 """
    form = EditPhoneForm()
    form.phone.model_update(form.model_dump())
    return app.restful.change_success()


@app_test.login_get("/device/phone")
def app_delete_phone():
    """ 删除手机 """
    form = GetPhoneForm()
    form.phone.delete()
    return app.restful.delete_success()
