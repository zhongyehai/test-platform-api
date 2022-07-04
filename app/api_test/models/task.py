# -*- coding: utf-8 -*-

from app.baseModel import BaseTask, db


class ApiTask(BaseTask):
    """ 定时任务表 """
    __abstract__ = False

    __tablename__ = 'api_test_task'

    project_id = db.Column(db.Integer, db.ForeignKey('api_test_project.id'), comment='所属的服务id')
    project = db.relationship('ApiProject', backref='tasks')
