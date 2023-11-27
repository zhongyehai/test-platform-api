# -*- coding: utf-8 -*-
from apps.base_model import BaseElement


class WebUiElement(BaseElement):
    """ 页面元素表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_element"
    __table_args__ = {"comment": "web-ui测试元素表"}
