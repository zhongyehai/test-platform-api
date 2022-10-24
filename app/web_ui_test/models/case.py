# -*- coding: utf-8 -*-

from app.baseModel import BaseCase, db
from app.web_ui_test.models.step import WebUiStep


class WebUiCase(BaseCase):
    """ 用例表 """
    __abstract__ = False

    __tablename__ = 'web_ui_test_case'

    set_id = db.Column(db.Integer, db.ForeignKey('web_ui_test_case_set.id'), comment='所属的用例集id')

    def delete_current_and_step(self):
        return self.delete_current_and_children(WebUiStep, 'case_id')
