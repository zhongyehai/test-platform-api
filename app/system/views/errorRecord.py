# -*- coding: utf-8 -*-
from app.baseView import AdminRequiredView
from app.system.blueprint import system_manage
from app.system.forms.errorRecord import GetSystemErrorRecordList
from app.system.models.errorRecord import SystemErrorRecord


class SystemErrorRecordListView(AdminRequiredView):

    def get(self):
        """ 获取系统报错记录的列表 """
        form = GetSystemErrorRecordList()
        return SystemErrorRecord.make_pagination(form)


system_manage.add_url_rule('/errorRecord/list',
                           view_func=SystemErrorRecordListView.as_view('SystemErrorRecordListView'))
