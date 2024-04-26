# -*- coding: utf-8 -*-
from sqlalchemy import String, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import NumFiled
from apps.enums import QueueTypeEnum


class QueueLink(NumFiled):
    """ 消息队列 """
    __tablename__ = "auto_test_queue_link"
    __table_args__ = {"comment": "消息队列链接管理"}
    # 消息队列链接属性
    queue_type: Mapped[QueueTypeEnum] = mapped_column(String(128), default="", comment="消息队列类型")
    instance_id: Mapped[str] = mapped_column(String(128), default="", comment="rocket_mq 对应的 instance_id")
    desc: Mapped[str] = mapped_column(String(512), nullable=True, default="", comment="描述")
    num: Mapped[int] = mapped_column(Integer, nullable=True, default=0, comment="排序字段")

    # rabbit_mq
    host: Mapped[str] = mapped_column(String(128), default="", comment="地址")
    port: Mapped[int] = mapped_column(Integer(), nullable=True, comment="端口")
    account: Mapped[str] = mapped_column(String(128), nullable=True, default="", comment="账号")
    password: Mapped[str] = mapped_column(String(128), nullable=True, default="", comment="密码")

    # rocket_mq
    access_id: Mapped[str] = mapped_column(String(128), nullable=True, default="", comment="access_id")
    access_key: Mapped[str] = mapped_column(String(128), nullable=True, default="", comment="access_key")


class QueueTopic(NumFiled):
    __tablename__ = "auto_test_queue_topic"
    __table_args__ = {"comment": "具体消息队列管理"}
    # 具体队列
    num: Mapped[int] = mapped_column(Integer, nullable=True, default=0, comment="排序字段")
    link_id: Mapped[int] = mapped_column(Integer(), nullable=True, comment="所属消息队列链接id")
    topic: Mapped[str] = mapped_column(String(128), default="", comment="rocket_mq对应topic，rabbit_mq对应queue_name")
    desc: Mapped[str] = mapped_column(String(512), nullable=True, default="", comment="描述")


class QueueMsgLog(NumFiled):
    """ 消息发送记录 """
    __tablename__ = "auto_test_queue_message_log"
    __table_args__ = {"comment": "消息发送记录表"}
    link_id: Mapped[int] = mapped_column(Integer(), comment="消息队列链接id")
    topic_id: Mapped[int] = mapped_column(Integer(), comment="topic id")
    tag: Mapped[str] = mapped_column(String(128), comment="tag")
    options: Mapped[dict] = mapped_column(JSON, comment="自定义内容")
    message: Mapped[dict] = mapped_column(JSON, comment="消息内容")
    status: Mapped[str] = mapped_column(Text(), comment="消息发送状态")
    response: Mapped[str] = mapped_column(Text(), comment="消息发送响应")
