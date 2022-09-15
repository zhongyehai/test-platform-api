# -*- coding: utf-8 -*-

from app.baseModel import BaseReport, db


class WebUiReport(BaseReport):
    """ 测试报告表 """
    __abstract__ = False

    __tablename__ = 'web_ui_test_report'

    project_id = db.Column(db.Integer, db.ForeignKey('web_ui_test_project.id'), comment='所属的服务id')
    project = db.relationship('WebUiProject', backref='reports')
