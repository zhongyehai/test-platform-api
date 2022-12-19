# -*- coding: utf-8 -*-
from app.baseModel import BaseModule


class WebUiModule(BaseModule):
    """ 模块表 """
    __abstract__ = False

    __tablename__ = "web_ui_test_module"
