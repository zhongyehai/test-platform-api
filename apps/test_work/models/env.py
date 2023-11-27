# -*- coding: utf-8 -*-
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import NumFiled


class Env(NumFiled):
    """ 测试环境资源表 """
    __tablename__ = "test_work_env"
    __table_args__ = {"comment": "环境、资源表"}

    business: Mapped[int] = mapped_column(Integer(), nullable=True, comment="业务线")
    name: Mapped[int] = mapped_column(String(255), comment="资源名")
    source_type: Mapped[int] = mapped_column(String(255), comment="资源类型，账号:account、地址:addr")
    value: Mapped[int] = mapped_column(String(255), comment="数据值")
    password: Mapped[int] = mapped_column(String(255), default='', comment="登录密码")
    desc: Mapped[int] = mapped_column(Text(), default='', comment="备注")
    parent: Mapped[int] = mapped_column(Integer(), nullable=True, comment="当source_type为账号时，所属资源id")
