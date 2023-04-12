# -*- coding: utf-8 -*-
from app.baseModel import BaseModule


class WebUiModule(BaseModule):
    """ 模块表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_module"
    __table_args__ = {"comment": "web-ui测试模块表"}
