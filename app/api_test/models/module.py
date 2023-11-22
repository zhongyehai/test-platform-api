# -*- coding: utf-8 -*-
from app.base_model import BaseModule, db


class ApiModule(BaseModule):
    """ 模块表 """
    __abstract__ = False
    __tablename__ = "api_test_module"
    __table_args__ = {"comment": "接口测试模块表"}

    controller = db.Column(db.String(255), comment="当前模块在swagger上的controller名字")
