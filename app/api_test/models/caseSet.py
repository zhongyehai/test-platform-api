# -*- coding: utf-8 -*-
from app.baseModel import BaseCaseSet


class ApiCaseSet(BaseCaseSet):
    """ 用例集表 """
    __abstract__ = False
    __tablename__ = "api_test_case_set"
    __table_args__ = {"comment": "接口测试用例集表"}
