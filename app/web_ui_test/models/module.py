# -*- coding: utf-8 -*-

from app.baseModel import BaseModule, db


class UiModule(BaseModule):
    """ 模块表 """
    __abstract__ = False

    __tablename__ = 'ui_test_module'

    project_id = db.Column(db.Integer, db.ForeignKey('ui_test_project.id'), comment='所属的服务id')
    project = db.relationship('UiProject', backref='modules')  # 一对多
