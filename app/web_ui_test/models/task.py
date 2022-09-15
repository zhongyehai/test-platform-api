# -*- coding: utf-8 -*-

from app.baseModel import BaseTask, db


class WebUiTask(BaseTask):
    """ 测试任务表 """
    __abstract__ = False

    __tablename__ = 'web_ui_test_task'

    project_id = db.Column(db.Integer, db.ForeignKey('web_ui_test_project.id'), comment='所属的服务id')
    project = db.relationship('WebUiProject', backref='tasks')
