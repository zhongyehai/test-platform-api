# -*- coding: utf-8 -*-
from flask import current_app as app

from app.assist.blueprint import assist
from app.assist.models.callBack import CallBack
from app.assist.forms.callBack import FindCallBackForm
from app.baseView import NotLoginView


class GetCallBackListView(NotLoginView):

    def get(self):
        """ 回调列表 """
        form = FindCallBackForm().do_validate()
        return app.restful.success(data=CallBack.make_pagination(form))


assist.add_url_rule("/callBack/list", view_func=GetCallBackListView.as_view("GetCallBackListView"))
