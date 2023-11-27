# -*- coding: utf-8 -*-
from apps.base_model import BaseCase


class WebUiCase(BaseCase):
    """ 用例表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_case"
    __table_args__ = {"comment": "web-ui测试用例表"}
