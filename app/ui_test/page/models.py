#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : models.py
# @Software: PyCharm
from app.baseModel import BaseModel, db


class UiPage(BaseModel):
    """ 页面表 """
    __tablename__ = 'ui_test_page'
    num = db.Column(db.Integer(), nullable=True, comment='页面序号')
    name = db.Column(db.String(255), nullable=True, comment='页面名称')
    addr = db.Column(db.String(255), nullable=True, comment='页面地址')
    desc = db.Column(db.Text(), default='', nullable=True, comment='页面描述')

    module_id = db.Column(db.Integer(), db.ForeignKey('ui_test_module.id'), comment='所属的模块id')
    project_id = db.Column(db.Integer(), nullable=True, comment='所属的项目id')

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.moduleId.data:
            filters.append(UiPage.module_id == form.moduleId.data)
        if form.name.data:
            filters.append(UiPage.name.like(f'%{form.name.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=UiPage.num.asc()
        )
