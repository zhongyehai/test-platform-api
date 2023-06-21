# -*- coding: utf-8 -*-
from app.baseModel import BaseReport, BaseReportStep


class WebUiReport(BaseReport):
    """ 测试报告表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_report"
    __table_args__ = {"comment": "web-ui测试报告表"}


class WebUiReportStep(BaseReportStep):
    """ 测试报告步骤表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_report_step"
    __table_args__ = {"comment": "web-ui测试报告的步骤数据表"}
