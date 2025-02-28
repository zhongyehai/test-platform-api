# -*- coding: utf-8 -*-
from sqlalchemy import Text, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseModel


class ShellCommandRecord(BaseModel):
    """ 自动化测试触发的问题记录 """
    __tablename__ = "auto_test_shell_command_record"
    __table_args__ = {"comment": "shell造数据"}

    file_content: Mapped[str] = mapped_column(Text(), default="", comment="文件数据")
    command: Mapped[str] = mapped_column(String(32), default="", comment="shell命令")
    command_out_put: Mapped[str] = mapped_column(Text(), default="", comment="shell执行结果")
    cmd_id: Mapped[str] = mapped_column(String(32), default="", comment="日志里面的cmdId")
    algo_instance_id: Mapped[str] = mapped_column(String(128), default="", comment="日志里面的algoInstanceId")
