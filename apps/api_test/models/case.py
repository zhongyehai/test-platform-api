# -*- coding: utf-8 -*-
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseCase


class ApiCase(BaseCase):
    """ 用例表 """
    __abstract__ = False
    __tablename__ = "api_test_case"
    __table_args__ = {"comment": "接口测试用例表"}

    headers: Mapped[dict] = mapped_column(
        JSON, default=[{"key": "", "value": "", "remark": ""}], comment="用例的头部信息")
