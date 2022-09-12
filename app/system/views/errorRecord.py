# -*- coding: utf-8 -*-
from app.baseView import AdminRequiredView
from app.system import system_manage
from app.system.forms.errorRecord import GetSystemErrorRecordList
from app.system.models.errorRecord import SystemErrorRecord

ns = system_manage.namespace("errorRecord", description="错误记录相关接口")


@ns.route('/list/')
class SystemErrorRecordListView(AdminRequiredView):

    def get(self):
        """ 获取系统报错记录的列表 """
        form = GetSystemErrorRecordList()
        return SystemErrorRecord.make_pagination(form)
