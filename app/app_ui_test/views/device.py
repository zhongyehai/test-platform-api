# -*- coding: utf-8 -*-
import requests
from flask import request, current_app as app

from app.app_ui_test.blueprint import app_test
from app.app_ui_test.models.device import AppUiRunServer as Server, AppUiRunPhone as Phone
from app.app_ui_test.forms.device import (
    AddServerForm, HasServerIdForm, EditServerForm, GetServerListForm,
    AddPhoneForm, HasPhoneIdForm, EditPhoneForm, GetPhoneListForm
)


@app_test.login_get("/device/server/list")
def app_get_run_server_list():
    """ 服务器列表 """
    form = GetServerListForm().do_validate()
    return app.restful.success(data=Server.make_pagination(form))


@app_test.login_put("/device/server/sort")
def app_change_server_sort():
    """ 更新服务器的排序 """
    Server.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
    return app.restful.success(msg="修改排序成功")


@app_test.login_post("/device/server/copy")
def app_copy_server():
    """ 复制服务器 """
    form = HasServerIdForm().do_validate()
    new_server = form.server.copy()
    return app.restful.success(msg="复制成功", data=new_server.to_dict())


@app_test.login_get("/device/server/run")
def app_run_server():
    """ 复制服务器 """
    """ 调appium服务器 """
    form = HasServerIdForm().do_validate()
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
    form = HasServerIdForm().do_validate()
    return app.restful.success(data=form.server.to_dict())


@app_test.login_post("/device/server")
def app_add_server():
    """ 新增服务 """
    form = AddServerForm().do_validate()
    form.num.data = Server.get_insert_num()
    new_server = Server().create(form.data)
    return app.restful.success(f"服务器【{form.name.data}】新建成功", new_server.to_dict())


@app_test.login_put("/device/server")
def app_change_server():
    """ 修改服务 """
    form = EditServerForm().do_validate()
    form.server.update(form.data)
    return app.restful.success(f"服务器【{form.name.data}】修改成功", form.server.to_dict())


@app_test.login_get("/device/server")
def app_delete_server():
    """ 删除服务 """
    form = HasServerIdForm().do_validate()
    form.server.delete()
    return app.restful.success(f"服务器【{form.server.name}】删除成功")


@app_test.login_get("/device/phone/list")
def app_get_phone_list():
    """ 手机列表 """
    form = GetPhoneListForm().do_validate()
    return app.restful.success(data=Phone.make_pagination(form))


@app_test.login_put("/device/phone/sort")
def app_change_phone_sort():
    """ 更新手机列表的排序 """
    Phone.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
    return app.restful.success(msg="修改排序成功")


@app_test.login_post("/device/phone/copy")
def app_copy_phone():
    """ 复制手机 """
    form = HasPhoneIdForm().do_validate()
    new_phone = form.phone.copy()
    return app.restful.success(msg="复制成功", data=new_phone.to_dict())


@app_test.login_get("/device/phone")
def app_get_phone():
    """ 获取手机 """
    form = HasPhoneIdForm().do_validate()
    return app.restful.success(data=form.phone.to_dict())


@app_test.login_post("/device/phone")
def app_add_phone():
    """ 新增手机 """
    form = AddPhoneForm().do_validate()
    form.num.data = Phone.get_insert_num()
    new_phone = Phone().create(form.data)
    return app.restful.success(f"手机【{form.name.data}】新建成功", new_phone.to_dict())


@app_test.login_put("/device/phone")
def app_change_phone():
    """ 修改手机 """
    form = EditPhoneForm().do_validate()
    form.phone.update(form.data)
    return app.restful.success(f"手机【{form.name.data}】修改成功", form.phone.to_dict())


@app_test.login_get("/device/phone")
def app_delete_phone():
    """ 删除手机 """
    form = HasPhoneIdForm().do_validate()
    form.phone.delete()
    return app.restful.success(f"手机【{form.phone.name}】删除成功")
