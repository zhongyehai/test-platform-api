# -*- coding: utf-8 -*-
from app.baseModel import db, SaveRequestLog


class SystemErrorRecord(SaveRequestLog):
    """ 系统错误记录表 """
    __tablename__ = "system_error_record"
    __table_args__ = {"comment": "系统错误记录表"}

    detail = db.Column(db.Text, nullable=True, comment="错误详情")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.url.data:
            filters.append(cls.url == form.url.data)
        if form.method.data:
            filters.append(cls.method == form.method.data)
        if form.request_user.data:
            filters.append(cls.create_user == form.request_user.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc()
        )
