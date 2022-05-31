#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/12/31 11:34
# @Author : ZhongYeHai
# @Site : 
# @File : models.py
# @Software: PyCharm
from app.baseModel import BaseModel, db


class SwaggerDiffRecord(BaseModel):
    """ yapi数据比对记录 """
    __tablename__ = 'swagger_diff_record'

    name = db.Column(db.String(255), comment='比对标识，全量比对，或者具体分组的比对')
    is_changed = db.Column(db.Integer, default=0, comment='对比结果，1有改变，0没有改变')
    diff_summary = db.Column(db.Text, comment='比对结果数据')

    @classmethod
    def make_pagination(cls, attr):
        """ 解析分页条件 """
        filters = []
        if attr.get('name'):
            filters.append(SwaggerDiffRecord.name.like(f'%{attr.get("name")}%'))
        if attr.get('create_user'):
            filters.append(SwaggerDiffRecord.create_user == attr.get('create_user'))
        return cls.pagination(
            page_num=attr.get('pageNum', 1),
            page_size=attr.get('pageSize', 20),
            filters=filters,
            order_by=cls.created_time.desc())
