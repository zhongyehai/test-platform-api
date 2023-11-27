# -*- coding: utf-8 -*-
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import SaveRequestLog


class SystemErrorRecord(SaveRequestLog):
    """ 系统错误记录表 """
    __tablename__ = "system_error_record"
    __table_args__ = {"comment": "系统错误记录表"}

    detail: Mapped[str] = mapped_column(Text, nullable=True, comment="错误详情")
