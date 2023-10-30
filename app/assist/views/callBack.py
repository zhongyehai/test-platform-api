# -*- coding: utf-8 -*-
from flask import current_app as app

from app.assist.blueprint import assist
from app.assist.models.callBack import CallBack
from app.assist.forms.callBack import FindCallBackForm


@assist.get("/callBack/list")
def assist_get_call_back_list():
    """ 回调列表 """
    form = FindCallBackForm().do_validate()
    return app.restful.success(data=CallBack.make_pagination(form))
