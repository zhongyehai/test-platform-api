# -*- coding: utf-8 -*-
from app.base_model import BaseApi, db


class WebUiPage(BaseApi):
    """ 页面表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_page"
    __table_args__ = {"comment": "web-ui测试页面表"}

    addr = db.Column(db.String(255), nullable=True, comment="地址")
