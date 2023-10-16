# -*- coding: utf-8 -*-
from datetime import datetime

from app.baseModel import BaseModel, db


class Hits(BaseModel):
    """ 自动化测试触发的问题记录 """
    __tablename__ = "auto_test_hits"
    __table_args__ = {"comment": "自动化测试触发问题记录"}

    date = db.Column(db.String(128), default=datetime.now, comment="问题触发日期")
    hit_type = db.Column(db.String(128), default="", comment="问题类型")
    hit_detail = db.Column(db.Text(), default="", comment="问题内容")
    test_type = db.Column(db.Text(), default="", comment="测试类型，接口、appUi、webUi")
    project_id = db.Column(db.Integer(), index=True, comment="服务id")
    env = db.Column(db.String(128), index=True, comment="运行环境")
    report_id = db.Column(db.Integer(), index=True, comment="测试报告id")
    desc = db.Column(db.Text(), comment="备注")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.date.data:
            filters.append(cls.date == form.date.data)
        if form.report_id.data:
            filters.append(cls.report_id == form.report_id.data)
        if form.hit_type.data:
            filters.append(cls.hit_type == form.hit_type.data)
        if form.test_type.data:
            filters.append(cls.test_type == form.test_type.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.id.desc()
        )
