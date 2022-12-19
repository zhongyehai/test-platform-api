# -*- coding: utf-8 -*-
from app.baseModel import BaseCase, db
from app.web_ui_test.models.step import WebUiStep


class WebUiCase(BaseCase):
    """ 用例表 """
    __abstract__ = False

    __tablename__ = "web_ui_test_case"

    def delete_current_and_step(self):
        return self.delete_current_and_children(WebUiStep, "case_id")
