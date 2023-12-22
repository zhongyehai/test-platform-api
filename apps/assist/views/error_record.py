# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import assist
from ..model_factory import FuncErrorRecord
from ..forms.error_record import GetErrorListForm, GetErrorForm


@assist.get("/error-record/list")
def assist_get_error_record_list():
    """ 错误列表 """
    form = GetErrorListForm()
    get_filed = [FuncErrorRecord.id, FuncErrorRecord.name, FuncErrorRecord.create_time, FuncErrorRecord.create_user]
    return app.restful.get_success(FuncErrorRecord.make_pagination(form, get_filed=get_filed))


@assist.get("/error-record")
def assist_get_error_record():
    """ 错误列表 """
    form = GetErrorForm()
    return app.restful.get_success(form.error_record.to_dict())
