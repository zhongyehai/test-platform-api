# -*- coding: utf-8 -*-
from flask import current_app as app

from app.assist.blueprint import assist
from app.assist.models.errorRecord import FuncErrorRecord
from app.assist.forms.errorRecord import FindErrorForm
from app.baseView import NotLoginView


class GetErrorRecordListView(NotLoginView):

    def get(self):
        """ 错误列表 """
        form = FindErrorForm().do_validate()
        return app.restful.success(data=FuncErrorRecord.make_pagination(form))


assist.add_url_rule("/errorRecord/list", view_func=GetErrorRecordListView.as_view("GetErrorRecordListView"))
