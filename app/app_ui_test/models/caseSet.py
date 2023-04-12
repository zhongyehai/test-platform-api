# -*- coding: utf-8 -*-
from app.baseModel import BaseCaseSet


class AppUiCaseSet(BaseCaseSet):
    """ 用例集表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_case_set"
    __table_args__ = {"comment": "APP测试用例集表"}
