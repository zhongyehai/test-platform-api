# -*- coding: utf-8 -*-
from flask import current_app as app

from app.assist.blueprint import assist
from app.assist.models.errorRecord import FuncErrorRecord
from app.assist.forms.errorRecord import FindErrorForm


@assist.get("/errorRecord/list")
def assist_get_error_record_list():
    """ 错误列表 """
    form = FindErrorForm().do_validate()
    return app.restful.success(data=FuncErrorRecord.make_pagination(form))
