#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/11/2 14:05
# @Author : ZhongYeHai
# @Site : 
# @File : models.py
# @Software: PyCharm
from app.baseModel import BaseModel, db


class KYMModule(BaseModel):
    """ KYM分析表 """
    __tablename__ = 'test_work_kym'

    project = db.Column(db.String(255), comment='服务名')
    kym = db.Column(db.Text, default='{}', comment='kym分析')

    def to_dict(self, *args, **kwargs):
        return super(KYMModule, self).to_dict(to_dict=['kym'])
