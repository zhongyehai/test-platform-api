# -*- coding: utf-8 -*-

from app.baseModel import BaseCaseSet, db


class ApiCaseSet(BaseCaseSet):
    """ 用例集表 """
    __abstract__ = False

    __tablename__ = 'api_test_case_set'

    project_id = db.Column(db.Integer, db.ForeignKey('api_test_project.id'), comment='所属的服务id')
    project = db.relationship('ApiProject', backref='api_test_set')  # 一对多

    cases = db.relationship('ApiCase', order_by='ApiCase.num.asc()', lazy='dynamic')
