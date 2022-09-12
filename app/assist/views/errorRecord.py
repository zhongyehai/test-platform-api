# -*- coding: utf-8 -*-
from flask import current_app as app

from app.assist import assist
from app.assist.models.errorRecord import FuncErrorRecord
from app.assist.forms.errorRecord import FindErrorForm
from app.baseView import NotLoginView

ns = assist.namespace("errorRecord", description="执行错误记录")


@ns.route('/list/')
class GetErrorRecordListView(NotLoginView):

    def get(self):
        """ 错误列表 """
        form = FindErrorForm()
        if form.validate():
            return app.restful.success(data=FuncErrorRecord.make_pagination(form))
        return app.restful.fail(form.get_error())
