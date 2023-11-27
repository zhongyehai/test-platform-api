# -*- coding: utf-8 -*-
from apps.base_model import BaseApi


class AppUiPage(BaseApi):
    """ 页面表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_page"
    __table_args__ = {"comment": "APP测试页面表"}
