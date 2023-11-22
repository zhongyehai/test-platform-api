# -*- coding: utf-8 -*-
from app.base_model import BaseElement, db


class WebUiElement(BaseElement):
    """ 页面元素表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_element"
    __table_args__ = {"comment": "web-ui测试元素表"}
