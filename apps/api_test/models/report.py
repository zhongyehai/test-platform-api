# -*- coding: utf-8 -*-
from apps.base_model import BaseReport, BaseReportCase, BaseReportStep


class ApiReport(BaseReport):
    """ 测试报告表 """
    __abstract__ = False
    __tablename__ = "api_test_report"
    __table_args__ = {"comment": "接口测试报告表"}


class ApiReportCase(BaseReportCase):
    """ 测试报告用例表 """
    __abstract__ = False
    __tablename__ = "api_test_report_case"
    __table_args__ = {"comment": "接口测试报告的用例数据表"}


class ApiReportStep(BaseReportStep):
    """ 测试报告步骤表 """
    __abstract__ = False
    __tablename__ = "api_test_report_step"
    __table_args__ = {"comment": "接口测试报告的步骤数据表"}
