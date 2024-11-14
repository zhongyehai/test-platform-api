# -*- coding: utf-8 -*-
from sqlalchemy import String, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import NumFiled, BaseModel
from apps.enums import QueueTypeEnum


class QueueInstance(NumFiled):
    """ 消息队列 """
    __tablename__ = "auto_test_queue_instance"
    __table_args__ = {"comment": "消息队列实例管理"}
    # 消息队列链接属性
    queue_type: Mapped[QueueTypeEnum] = mapped_column(String(128), default="", comment="消息队列类型")
    instance_id: Mapped[str] = mapped_column(String(128), default="test_platform_client", comment="rocket_mq 对应的 instance_id")
    desc: Mapped[str] = mapped_column(String(512), nullable=True, default="", comment="描述")

    # rabbit_mq
    host: Mapped[str] = mapped_column(String(128), default="", comment="rabbit_mq 地址")
    port: Mapped[int] = mapped_column(Integer(), nullable=True, comment="rabbit_mq 端口")
    account: Mapped[str] = mapped_column(String(128), nullable=True, default="", comment="rabbit_mq 账号")
    password: Mapped[str] = mapped_column(String(128), nullable=True, default="", comment="rabbit_mq 密码")

    # rocket_mq
    access_id: Mapped[str] = mapped_column(String(128), nullable=True, default="", comment="rocket_mq access_id")
    access_key: Mapped[str] = mapped_column(String(128), nullable=True, default="", comment="rocket_mq access_key")


class QueueTopic(NumFiled):
    __tablename__ = "auto_test_queue_topic"
    __table_args__ = {"comment": "topic 管理"}
    instance_id: Mapped[int] = mapped_column(Integer(), nullable=True, comment="rocket_mq 实例数据id")
    topic: Mapped[str] = mapped_column(String(128), default="", comment="rocket_mq topic，rabbit_mq queue_name")
    desc: Mapped[str] = mapped_column(String(512), nullable=True, default="", comment="描述")


class QueueMsgLog(BaseModel):
    """ 消息发送记录 """
    __tablename__ = "auto_test_queue_message_log"
    __table_args__ = {"comment": "消息发送记录表"}
    instance_id: Mapped[int] = mapped_column(Integer(), comment="消息队列实例数据id")
    topic_id: Mapped[int] = mapped_column(Integer(), comment="topic id")
    tag: Mapped[str] = mapped_column(String(128), comment="tag")
    options: Mapped[dict] = mapped_column(JSON, comment="自定义内容")
    message_type: Mapped[str] = mapped_column(String(8), comment="消息类型")
    message: Mapped[dict] = mapped_column(JSON, comment="消息内容")
    status: Mapped[str] = mapped_column(Text(), comment="消息发送状态")
    response: Mapped[str] = mapped_column(Text(), comment="消息发送响应")
