# -*- coding: utf-8 -*-

from app.baseModel import BaseCase, db
from app.web_ui_test.models.step import UiStep


class UiCase(BaseCase):
    """ 用例表 """
    __abstract__ = False

    __tablename__ = 'ui_test_case'

    cookies = db.Column(db.Text(), default='[{"key": "", "value": "", "remark": ""}]', comment='cookie')
    session_storage = db.Column(db.Text(), default='[{"key": "", "value": "", "remark": ""}]', comment='session_storage')
    local_storage = db.Column(db.Text(), default='[{"key": "", "value": "", "remark": ""}]', comment='local_storage')

    set_id = db.Column(db.Integer, db.ForeignKey('ui_test_case_set.id'), comment='所属的用例集id')

    def delete_current_and_step(self):
        return self.delete_current_and_children(UiStep, 'case_id')
