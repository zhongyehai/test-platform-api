# -*- coding: utf-8 -*-
from app.base_model import BaseCaseSuite


class WebUiCaseSuite(BaseCaseSuite):
    """ 用例集表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_case_suite"
    __table_args__ = {"comment": "web-ui测试用例集表"}
