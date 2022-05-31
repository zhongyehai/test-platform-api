# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField

from app.baseForm import BaseForm


class FindErrorForm(BaseForm):
    """ 查找服务form """
    name = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()
