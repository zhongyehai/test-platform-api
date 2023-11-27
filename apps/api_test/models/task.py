# -*- coding: utf-8 -*-
from apps.base_model import BaseTask


class ApiTask(BaseTask):
    """ 定时任务表 """
    __abstract__ = False
    __tablename__ = "api_test_task"
    __table_args__ = {"comment": "接口测试任务表"}
