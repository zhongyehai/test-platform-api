# -*- coding: utf-8 -*-

from app.baseModel import BaseModule, db


class ApiModule(BaseModule):
    """ 模块表 """
    __abstract__ = False

    __tablename__ = 'api_test_module'

    yapi_id = db.Column(db.Integer(), comment='当前模块在yapi平台对应的模块id')

    project_id = db.Column(db.Integer, db.ForeignKey('api_test_project.id'), comment='所属的服务id')
    project = db.relationship('ApiProject', backref='modules')  # 一对多
