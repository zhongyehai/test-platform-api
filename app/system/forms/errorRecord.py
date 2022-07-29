# -*- coding: utf-8 -*-
from wtforms import IntegerField, StringField

from app.baseForm import BaseForm


class GetSystemErrorRecordList(BaseForm):
    """ 获取系统报错列表 """
    url = StringField()
    method = StringField()
    request_user = IntegerField()
    pageNum = IntegerField()
    pageSize = IntegerField()
