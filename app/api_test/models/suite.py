# -*- coding: utf-8 -*-
from app.baseModel import BaseCaseSuite


class ApiCaseSuite(BaseCaseSuite):
    """ 用例集表 """
    __abstract__ = False
    __tablename__ = "api_test_case_suite"
    __table_args__ = {"comment": "接口测试用例集表"}

