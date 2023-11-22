# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import test_work
from ..forms.env import GetEnvListForm, GetEnvForm, DeleteEnvForm, AddEnvForm, ChangeEnvForm, GetAccountListForm, \
    GetAccountForm, AddAccountForm, ChangeAccountForm, DeleteAccountForm
from ..model_factory import Env


@test_work.post("/env/list")
def test_work_get_env_list():
    """ 获取数据列表 """
    form = GetEnvListForm()
    get_filed = [Env.id, Env.business, Env.name, Env.value, Env.desc]
    return app.restful.get_success(Env.make_pagination(form, get_filed=get_filed))


@test_work.login_get("/env")
def test_work_get_env():
    """ 获取数据 """
    form = GetEnvForm()
    return app.restful.get_success(form.env.to_dict())


@test_work.login_post("/env")
def test_work_add_env():
    """ 新增数据 """
    form = AddEnvForm()
    Env.model_batch_create(form.data_list)
    return app.restful.add_success()


@test_work.login_put("/env")
def test_work_change_env():
    """ 修改数据 """
    form = ChangeEnvForm()
    form.env.model_update(form.model_dump())
    return app.restful.change_success()


@test_work.login_delete("/env")
def test_work_delete_env():
    """ 删除数据 """
    form = DeleteEnvForm()
    form.env.delete()
    return app.restful.delete_success()


@test_work.post("/account/list")
def test_work_get_account_list():
    """ 获取数据列表 """
    form = GetAccountListForm()
    get_filed = [Env.id, Env.name, Env.value, Env.password, Env.desc]
    return app.restful.get_success(Env.make_pagination(form, get_filed=get_filed))


@test_work.login_get("/account")
def test_work_get_account():
    """ 获取数据 """
    form = GetAccountForm()
    return app.restful.get_success(form.env.to_dict())


@test_work.login_post("/account")
def test_work_add_account():
    """ 新增数据 """
    form = AddAccountForm()
    Env.model_batch_create(form.data_list)
    return app.restful.add_success()


@test_work.login_put("/account")
def test_work_change_account():
    """ 修改数据 """
    form = ChangeAccountForm()
    form.env.model_update(form.model_dump())
    return app.restful.change_success()


@test_work.login_delete("/account")
def test_work_delete_account():
    """ 删除数据 """
    form = DeleteAccountForm()
    form.env.delete()
    return app.restful.delete_success()
