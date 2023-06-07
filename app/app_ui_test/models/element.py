# -*- coding: utf-8 -*-
from app.baseModel import BaseApi, db


class AppUiElement(BaseApi):
    """ 页面元素表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_element"
    __table_args__ = {"comment": "APP测试元素表"}

    by = db.Column(db.String(255), nullable=True, comment="定位方式")
    element = db.Column(db.Text(), default="", nullable=True, comment="元素值")
    wait_time_out = db.Column(db.Integer(), default=3, nullable=True, comment="等待元素出现的时间，默认3秒")
    page_id = db.Column(db.Integer(), comment="所属的页面id")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.pageId.data:
            filters.append(cls.page_id == form.pageId.data)
        if form.name.data:
            filters.append(cls.name.like(f"%{form.name.data}%"))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )
