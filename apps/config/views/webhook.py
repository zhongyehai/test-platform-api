# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import config_blueprint
from ...base_form import ChangeSortForm
from ..model_factory import WebHook
from ..forms.webhook import GetWebHookForm, DeleteWebHookForm, PostWebHookForm, PutWebHookForm, GetWebHookListForm


@config_blueprint.get("/webhook/list")
def config_get_webhook_list():
    form = GetWebHookListForm()
    if form.detail:
        get_filed = [WebHook.id, WebHook.name, WebHook.addr, WebHook.webhook_type, WebHook.desc]
    else:
        get_filed = [WebHook.id, WebHook.name, WebHook.webhook_type]
    return app.restful.get_success(WebHook.make_pagination(form, get_filed=get_filed))


@config_blueprint.login_put("/webhook/sort")
def config_change_webhook_sort():
    """ 修改排序 """
    form = ChangeSortForm()
    WebHook.change_sort(**form.model_dump())
    return app.restful.change_success()


@config_blueprint.login_get("/webhook")
def config_get_webhook():
    """ 获取webhook """
    form = GetWebHookForm()
    return app.restful.get_success(form.webhook.to_dict())


@config_blueprint.login_post("/webhook")
def config_add_webhook():
    """ 新增webhook """
    form = PostWebHookForm()
    WebHook.model_batch_create([data.model_dump() for data in form.data_list])
    return app.restful.add_success()


@config_blueprint.login_put("/webhook")
def config_change_webhook():
    """ 修改webhook """
    form = PutWebHookForm()
    form.webhook.model_update(form.model_dump())
    return app.restful.change_success()


@config_blueprint.login_delete("/webhook")
def config_delete_webhook():
    """ 删除webhook """
    form = DeleteWebHookForm()
    form.webhook.delete()
    return app.restful.delete_success()
