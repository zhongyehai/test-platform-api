# -*- coding: utf-8 -*-
from app.baseModel import BaseCase, db
from app.app_ui_test.models.step import AppUiStep


class AppUiCase(BaseCase):
    """ 用例表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_case"
    __table_args__ = {"comment": "APP测试用例表"}

    def delete_current_and_step(self):
        return self.delete_current_and_children(AppUiStep, "case_id")
