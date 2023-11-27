# -*- coding: utf-8 -*-
from apps.base_model import BaseCase


class AppUiCase(BaseCase):
    """ 用例表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_case"
    __table_args__ = {"comment": "APP测试用例表"}
