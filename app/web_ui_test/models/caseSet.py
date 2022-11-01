# -*- coding: utf-8 -*-

from app.baseModel import BaseCaseSet, db


class WebUiCaseSet(BaseCaseSet):
    """ 用例集表 """
    __abstract__ = False

    __tablename__ = 'web_ui_test_case_set'

    project_id = db.Column(db.Integer, db.ForeignKey('web_ui_test_project.id'), comment='所属的服务id')
    project = db.relationship('WebUiProject', backref='case_sets')  # 一对多

    cases = db.relationship('WebUiCase', order_by='WebUiCase.num.asc()', lazy='dynamic')
