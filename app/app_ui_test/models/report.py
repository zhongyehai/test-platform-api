# -*- coding: utf-8 -*-
from app.baseModel import BaseReport


class AppUiReport(BaseReport):
    """ 测试报告表 """
    __abstract__ = False

    __tablename__ = "app_ui_test_report"
