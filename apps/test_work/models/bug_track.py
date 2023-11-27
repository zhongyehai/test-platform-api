# -*- coding: utf-8 -*-
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import NumFiled


class BugTrack(NumFiled):
    """ 生产Bug跟踪表 """
    __tablename__ = "test_work_bug_track"
    __table_args__ = {"comment": "生产Bug跟踪表"}

    business_id: Mapped[int] = mapped_column(Integer(), index=True, comment="业务线id")
    name: Mapped[int] = mapped_column(String(255), default='', comment="bug名")
    detail: Mapped[str] = mapped_column(Text(), default='', comment="bug详情")
    iteration: Mapped[str] = mapped_column(String(128), default='', comment="迭代")
    bug_from: Mapped[str] = mapped_column(String(128), default='', comment="缺陷来源")
    trigger_time: Mapped[str] = mapped_column(String(128), default='', comment="发现时间")
    manager: Mapped[int] = mapped_column(Integer(), default=None, comment="跟进负责人")
    reason: Mapped[str] = mapped_column(String(128), default='', comment="原因")
    solution: Mapped[str] = mapped_column(String(128), default='', comment="解决方案")
    status: Mapped[str] = mapped_column(
        String(64), default='todo', comment="bug状态，todo：待解决、doing：解决中、done：已解决")
    replay: Mapped[int] = mapped_column(Integer(), default=0, comment="是否复盘，0：未复盘，1：已复盘")
    conclusion: Mapped[str] = mapped_column(Text(), default='', comment="复盘结论")
