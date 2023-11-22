# -*- coding: utf-8 -*-
from app.base_model import BaseCaseSuite


class AppUiCaseSuite(BaseCaseSuite):
    """ 用例集表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_case_suite"
    __table_args__ = {"comment": "APP测试用例集表"}
