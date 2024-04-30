# -*- coding: utf-8 -*-
from datetime import datetime

from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import NumFiled
from apps.enums import TodoListEnum


class Todo(NumFiled):
    """ 待处理事项 """
    __tablename__ = "test_work_todo"
    __table_args__ = {"comment": "待处理任务"}
    status: Mapped[TodoListEnum] = mapped_column(String(128), default=TodoListEnum.todo, comment="状态")
    title: Mapped[str] = mapped_column(String(512), nullable=True, default="", comment="任务title")
    done_user: Mapped[int] = mapped_column(Integer(), nullable=True, comment="完成人")
    done_time: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="完成时间")
    # tags: Mapped[str] = mapped_column(String(512), nullable=True, default="", comment="tag")
    detail: Mapped[str] = mapped_column(String(2048), nullable=True, default="", comment="任务详情")
