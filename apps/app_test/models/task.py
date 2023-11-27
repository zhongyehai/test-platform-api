# -*- coding: utf-8 -*-
from apps.base_model import BaseTask


class AppUiTask(BaseTask):
    """ 测试任务表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_task"
    __table_args__ = {"comment": "APP测试任务表"}
