# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import manage
from ..forms.env import GetEnvListForm, GetEnvForm, DeleteEnvForm, AddEnvForm, ChangeEnvForm, GetAccountListForm, \
    GetAccountForm, AddAccountForm, ChangeAccountForm, DeleteAccountForm
from ..model_factory import Env


@manage.get("/env/list")
def manage_get_env_list():
    """ 获取数据列表 """
    form = GetEnvListForm()
    get_filed = [Env.id, Env.business, Env.name, Env.value, Env.desc]
    return app.restful.get_success(Env.make_pagination(form, get_filed=get_filed))


@manage.login_get("/env")
def manage_get_env():
    """ 获取数据 """
    form = GetEnvForm()
    return app.restful.get_success(form.env.to_dict())


@manage.login_post("/env")
def manage_add_env():
    """ 新增数据 """
    form = AddEnvForm()
    Env.model_batch_create(form.data_list)
    return app.restful.add_success()


@manage.login_put("/env")
def manage_change_env():
    """ 修改数据 """
    form = ChangeEnvForm()
    form.env.model_update(form.model_dump())
    return app.restful.change_success()


@manage.login_delete("/env")
def manage_delete_env():
    """ 删除数据 """
    form = DeleteEnvForm()
    form.env.delete()
    return app.restful.delete_success()


@manage.get("/account/list")
def manage_get_account_list():
    """ 获取数据列表 """
    form = GetAccountListForm()
    get_filed = [Env.id, Env.name, Env.value, Env.password, Env.desc]
    return app.restful.get_success(Env.make_pagination(form, get_filed=get_filed))


@manage.login_get("/account")
def manage_get_account():
    """ 获取数据 """
    form = GetAccountForm()
    return app.restful.get_success(form.env.to_dict())


@manage.login_post("/account")
def manage_add_account():
    """ 新增数据 """
    form = AddAccountForm()
    Env.model_batch_create(form.data_list)
    return app.restful.add_success()


@manage.login_put("/account")
def manage_change_account():
    """ 修改数据 """
    form = ChangeAccountForm()
    form.env.model_update(form.model_dump())
    return app.restful.change_success()


@manage.login_delete("/account")
def manage_delete_account():
    """ 删除数据 """
    form = DeleteAccountForm()
    form.env.delete()
    return app.restful.delete_success()
