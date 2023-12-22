# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import system_manage
from ..forms.error_record import GetSystemErrorRecordListForm, GetSystemErrorRecordForm
from ..model_factory import SystemErrorRecord


@system_manage.admin_get("/error-record/list")
def system_manage_get_error_record_list():
    """ 获取系统报错记录的列表 """
    form = GetSystemErrorRecordListForm()
    get_filed = [SystemErrorRecord.id, SystemErrorRecord.create_time, SystemErrorRecord.create_user,
                 SystemErrorRecord.method, SystemErrorRecord.url]
    return app.restful.get_success(SystemErrorRecord.make_pagination(form, get_filed=get_filed))


@system_manage.admin_get("/error-record")
def system_manage_get_error_record():
    """ 获取系统报错记录 """
    form = GetSystemErrorRecordForm()
    return app.restful.get_success(form.error_record.to_dict())
