# -*- coding: utf-8 -*-
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseStep, ExtractsFiled, ValidatesFiled


class AppUiStep(BaseStep, ExtractsFiled, ValidatesFiled):
    """ 测试步骤表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_step"
    __table_args__ = {"comment": "APP测试步骤表"}

    wait_time_out: Mapped[int] = mapped_column(
        Integer(), default=10, nullable=True, comment="等待元素出现的时间，默认10秒")
    execute_type: Mapped[str] = mapped_column(String(255), nullable=True, comment="执行方式")
    send_keys: Mapped[str] = mapped_column(String(255), nullable=True, comment="要输入的文本内容")
    element_id: Mapped[int] = mapped_column(Integer(), nullable=True, comment="步骤所引用的元素的id")
