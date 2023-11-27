# -*- coding: utf-8 -*-
from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.system.model_factory import SaveRequestLog


class CallBack(SaveRequestLog):
    """ 自动化测试回调记录 """
    __tablename__ = "auto_test_call_back"
    __table_args__ = {"comment": "自动化测试回调流水线记录"}

    status: Mapped[int] = mapped_column(Integer(), default=1, comment="回调状态, 0失败，1回调中，2成功")
    result: Mapped[str] = mapped_column(Text, default='', nullable=True, comment="回调响应")

    def success(self, call_back_res):
        """ 回调成功 """
        self.model_update({"status": 2, "result": call_back_res})

    def fail(self):
        """ 回调失败 """
        self.model_update({"status": 0})
