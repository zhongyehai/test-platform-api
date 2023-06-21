# -*- coding: utf-8 -*-
from app.baseModel import BaseReport, BaseReportStep


class AppUiReport(BaseReport):
    """ 测试报告表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_report"
    __table_args__ = {"comment": "APP测试报告表"}


class AppUiReportStep(BaseReportStep):
    """ 测试报告步骤表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_report_step"
    __table_args__ = {"comment": "APP测试报告的步骤数据表"}
