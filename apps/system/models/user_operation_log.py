# -*- coding: utf-8 -*-
from apps.base_model import SaveRequestLog


class UserOperationLog(SaveRequestLog):
    """ 用户操作记录表 """
    __tablename__ = "system_user_operation_log"
    __table_args__ = {"comment": "用户操作记录表"}
