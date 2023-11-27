# -*- coding: utf-8 -*-
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseModule


class ApiModule(BaseModule):
    """ 模块表 """
    __abstract__ = False
    __tablename__ = "api_test_module"
    __table_args__ = {"comment": "接口测试模块表"}

    controller: Mapped[str] = mapped_column(String(255), nullable=True, comment="当前模块在swagger上的controller名字")
