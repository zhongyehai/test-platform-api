# -*- coding: utf-8 -*-
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import NumFiled
from apps.enums import TodoListEnum


class Todo(NumFiled):
    """ 待处理事项 """
    __tablename__ = "test_work_todo"
    __table_args__ = {"comment": "待处理任务"}
    status: Mapped[TodoListEnum] = mapped_column(String(128), default=TodoListEnum.todo, comment="状态")
    title: Mapped[str] = mapped_column(String(512), nullable=True, default="", comment="任务title")
    # tags: Mapped[str] = mapped_column(String(512), nullable=True, default="", comment="tag")
    detail: Mapped[str] = mapped_column(String(2048), nullable=True, default="", comment="任务详情")
