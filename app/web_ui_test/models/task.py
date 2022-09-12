# -*- coding: utf-8 -*-

from app.baseModel import BaseTask, db


class UiTask(BaseTask):
    """ 测试任务表 """
    __abstract__ = False

    __tablename__ = 'ui_test_task'

    project_id = db.Column(db.Integer, db.ForeignKey('ui_test_project.id'), comment='所属的服务id')
    project = db.relationship('UiProject', backref='tasks')
