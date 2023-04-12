# -*- coding: utf-8 -*-
from app.baseModel import BaseApi, db


class WebUiPage(BaseApi):
    """ 页面表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_page"
    __table_args__ = {"comment": "web-ui测试页面表"}

    addr = db.Column(db.String(255), nullable=True, comment="地址")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.moduleId.data:
            filters.append(cls.module_id == form.moduleId.data)
        if form.name.data:
            filters.append(cls.name.like(f"%{form.name.data}%"))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )
