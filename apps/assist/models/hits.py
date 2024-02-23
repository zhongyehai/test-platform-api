# -*- coding: utf-8 -*-
from datetime import datetime

from sqlalchemy import Text, String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseModel


class Hits(BaseModel):
    """ 自动化测试触发的问题记录 """
    __tablename__ = "auto_test_hits"
    __table_args__ = {"comment": "自动化测试触发问题记录"}

    date: Mapped[str] = mapped_column(String(128), default=datetime.now, comment="问题触发日期")
    hit_type: Mapped[str] = mapped_column(String(128), default="", comment="问题类型")
    hit_detail: Mapped[str] = mapped_column(Text(), default="", comment="问题内容")
    test_type: Mapped[str] = mapped_column(Text(), default="", comment="测试类型，接口、app、ui")
    project_id: Mapped[int] = mapped_column(Integer(), index=True, comment="服务id")
    env: Mapped[str] = mapped_column(String(128), index=True, comment="运行环境")
    report_id: Mapped[int] = mapped_column(Integer(), index=True, comment="测试报告id")
    desc: Mapped[str] = mapped_column(Text(), nullable=True, comment="备注")
