# -*- coding: utf-8 -*-
from app.baseModel import BaseCaseSet


class WebUiCaseSet(BaseCaseSet):
    """ 用例集表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_case_set"
    __table_args__ = {"comment": "web-ui测试用例集表"}
