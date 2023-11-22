# -*- coding: utf-8 -*-
from app.base_model import BaseTask, db


class WebUiTask(BaseTask):
    """ 测试任务表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_task"
    __table_args__ = {"comment": "web-ui测试任务表"}
