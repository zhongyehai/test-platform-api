# -*- coding: utf-8 -*-
from app.baseModel import BaseTask, db


class AppUiTask(BaseTask):
    """ 测试任务表 """
    __abstract__ = False

    __tablename__ = "app_ui_test_task"
