# -*- coding: utf-8 -*-
from app.system import system_manage
from app.system.forms.errorRecord import GetSystemErrorRecordList
from app.system.models.errorRecord import SystemErrorRecord


@system_manage.route('/errorRecord/list')
def system_error_record_list_is_admin_required():
    """ 系统报错的列表 """
    form = GetSystemErrorRecordList()
    return SystemErrorRecord.make_pagination(form)
