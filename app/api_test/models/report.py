# -*- coding: utf-8 -*-
from app.baseModel import BaseReport


class ApiReport(BaseReport):
    """ 测试报告表 """
    __abstract__ = False

    __tablename__ = "api_test_report"
