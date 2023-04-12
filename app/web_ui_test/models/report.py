# -*- coding: utf-8 -*-
from app.baseModel import BaseReport


class WebUiReport(BaseReport):
    """ 测试报告表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_report"
    __table_args__ = {"comment": "web-ui测试报告表"}

