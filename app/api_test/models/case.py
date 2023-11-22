# -*- coding: utf-8 -*-
from app.base_model import BaseCase, db


class ApiCase(BaseCase):
    """ 用例表 """
    __abstract__ = False
    __tablename__ = "api_test_case"
    __table_args__ = {"comment": "接口测试用例表"}

    headers = db.Column(db.JSON, default=[{"key": "", "value": "", "remark": ""}], comment="用例的头部信息")
