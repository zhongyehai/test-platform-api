# -*- coding: utf-8 -*-
import requests
from flask import current_app as app

from ..blueprint import config_blueprint
from ...base_form import ChangeSortForm
from ..model_factory import WebHook
from ..forms.webhook import GetWebHookForm, DeleteWebHookForm, PostWebHookForm, PutWebHookForm, GetWebHookListForm
from ...enums import WebHookTypeEnum
from utils.message.template import debug_msg_ding_ding, debug_msg_we_chat


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


@config_blueprint.login_post("/webhook/debug")
def config_debug_webhook():
    """ 调试webhook """
    form = GetWebHookForm()
    match form.webhook.webhook_type:
        case WebHookTypeEnum.ding_ding:
            msg = debug_msg_ding_ding()
        case WebHookTypeEnum.we_chat:
            msg = debug_msg_we_chat()
        case _:
            return app.restful.fail("webhook类型暂不支持")
    addr = form.webhook.build_webhook_addr(form.webhook.webhook_type, form.webhook.addr, form.webhook.secret)
    try:
        return app.restful.success(requests.post(addr, json=msg).text)
    except Exception as e:
        return app.restful.fail("调试触发失败，请检查地址是否正确，网络是否通畅")


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
