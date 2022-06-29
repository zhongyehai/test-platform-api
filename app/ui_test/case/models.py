# -*- coding: utf-8 -*-

from app.baseModel import BaseCase, db


class UiCase(BaseCase):
    """ 用例表 """
    __abstract__ = False

    __tablename__ = 'ui_test_case'

    set_id = db.Column(db.Integer, db.ForeignKey('ui_test_case_set.id'), comment='所属的用例集id')
