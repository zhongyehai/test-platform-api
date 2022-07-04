# -*- coding: utf-8 -*-

from app.baseModel import BaseCase, db


class ApiCase(BaseCase):
    """ 用例表 """
    __abstract__ = False

    __tablename__ = 'api_test_case'

    headers = db.Column(db.Text(), comment='用例级的头部信息')
    set_id = db.Column(db.Integer, db.ForeignKey('api_test_case_set.id'), comment='所属的用例集id')
