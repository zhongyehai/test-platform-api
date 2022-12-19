# -*- coding: utf-8 -*-
from app.baseModel import BaseTask, db


class ApiTask(BaseTask):
    """ 定时任务表 """
    __abstract__ = False

    __tablename__ = "api_test_task"
