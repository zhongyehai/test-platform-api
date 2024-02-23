# -*- coding: utf-8 -*-
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import NumFiled
from apps.enums import QueueTypeEnum


class Queue(NumFiled):
    """ 消息队列 """
    __tablename__ = "auto_test_queue"
    __table_args__ = {"comment": "消息队列管理"}
    # 消息队列链接属性
    queue_type: Mapped[QueueTypeEnum] = mapped_column(String(128), default="", comment="消息队列类型")
    host: Mapped[str] = mapped_column(String(128), default="", comment="地址")
    port: Mapped[int] = mapped_column(Integer(), default=5672, comment="端口")
    account: Mapped[str] = mapped_column(String(128), default="", comment="账号")
    password: Mapped[str] = mapped_column(String(128), default="", comment="密码")
    desc: Mapped[str] = mapped_column(String(512), nullable=True, default="", comment="描述")
    # 具体队列
    link_id: Mapped[int] = mapped_column(Integer(), nullable=True, comment="所属消息队列链接id")
    queue_name: Mapped[str] = mapped_column(String(128), default="", comment="消息队列名")


class QueueMsgLog(NumFiled):
    """ 消息发送记录 """
    __tablename__ = "auto_test_queue_message_log"
    __table_args__ = {"comment": "消息发送记录表"}
    queue_id: Mapped[int] = mapped_column(Integer(), comment="消息队列id")
    message: Mapped[str] = mapped_column(Text(), comment="消息内容")
