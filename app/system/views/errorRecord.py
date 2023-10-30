# -*- coding: utf-8 -*-
from app.system.blueprint import system_manage
from app.system.forms.errorRecord import GetSystemErrorRecordList
from app.system.models.errorRecord import SystemErrorRecord


@system_manage.admin_get("/errorRecord/list")
def system_manage_get_error_record_list():
    """ 获取系统报错记录的列表 """
    form = GetSystemErrorRecordList()
    return SystemErrorRecord.make_pagination(form)
