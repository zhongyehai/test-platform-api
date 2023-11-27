# -*- coding: utf-8 -*-
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseApi


class WebUiPage(BaseApi):
    """ 页面表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_page"
    __table_args__ = {"comment": "web-ui测试页面表"}

    addr: Mapped[str] = mapped_column(String(255), nullable=True, comment="地址")
