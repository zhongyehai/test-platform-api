# -*- coding: utf-8 -*-
from apps.base_model import BaseModule


class AppUiModule(BaseModule):
    """ 模块表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_module"
    __table_args__ = {"comment": "APP测试模块表"}
