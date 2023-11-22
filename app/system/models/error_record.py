# -*- coding: utf-8 -*-
from app.base_model import db, SaveRequestLog


class SystemErrorRecord(SaveRequestLog):
    """ 系统错误记录表 """
    __tablename__ = "system_error_record"
    __table_args__ = {"comment": "系统错误记录表"}

    detail = db.Column(db.Text, nullable=True, comment="错误详情")
