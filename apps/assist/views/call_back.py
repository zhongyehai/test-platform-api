# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import assist
from ..model_factory import CallBack
from ..forms.call_back import GetCallBackListForm, GetCallBackForm


@assist.get("/call-back/list")
def assist_get_call_back_list():
    """ 回调列表 """
    form = GetCallBackListForm()
    get_filed = [CallBack.id, CallBack.create_time, CallBack.url, CallBack.status]
    return app.restful.get_success(CallBack.make_pagination(form, get_filed=get_filed))


@assist.get("/call-back")
def assist_get_call_back():
    """ 回调列表 """
    form = GetCallBackForm()
    return app.restful.get_success(form.call_back.to_dict())
