# -*- coding: utf-8 -*-
from sqlalchemy import Text, String, LargeBinary, Integer
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseModel


class ApschedulerJobs(BaseModel):
    """ apscheduler任务表，防止执行数据库迁移的时候，把定时任务删除了 """
    __tablename__ = "apscheduler_jobs"
    __table_args__ = {"comment": "定时任务执行计划表"}

    id: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    next_run_time: Mapped[str] = mapped_column(String(128), comment="任务下一次运行时间")
    job_state: Mapped[str] = mapped_column(LargeBinary(length=(2 ** 32) - 1), comment="任务详情")


class JobRunLog(BaseModel):
    """ 系统job执行记录 """
    __tablename__ = "system_job_run_log"
    __table_args__ = {"comment": "系统job执行记录"}

    func_name: Mapped[str] = mapped_column(String(255), comment="执行方法")
    status: Mapped[int] = mapped_column(Integer(), default=1, comment="执行状态：0失败、1执行中、2执行成功")
    business_id: Mapped[int] = mapped_column(Integer(), default=None, comment="业务线id")
    detail: Mapped[str] = mapped_column(Text, default=None, comment="执行结果数据")

    def run_fail(self, detail=None):
        """ 执行失败 """
        self.model_update({"status": 0, "detail": self.dumps(detail)})

    def run_success(self, detail):
        """ 执行成功 """
        self.model_update({"status": 2, "detail": self.dumps(detail)})
