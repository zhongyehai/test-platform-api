# -*- coding: utf-8 -*-
from app.baseModel import SaveRequestLog, db


class UserOperationLog(SaveRequestLog):
    """ 用户操作记录表 """
    __tablename__ = "system_user_operation_log"
