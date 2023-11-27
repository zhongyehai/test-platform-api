# -*- coding: utf-8 -*-

from sqlalchemy import Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseModel


class SwaggerPullLog(BaseModel):
    """ swagger拉取日志 """
    __tablename__ = "swagger_pull_log"
    __table_args__ = {"comment": "swagger拉取日志"}

    status: Mapped[int] = mapped_column(Integer(), default=1, comment="拉取结果，0失败，1拉取中，2拉取成功")
    project_id: Mapped[int] = mapped_column(Integer(), comment="服务id")
    desc: Mapped[str] = mapped_column(Text(), nullable=True, comment="备注")
    pull_args: Mapped[dict] = mapped_column(JSON, default=[], nullable=True, comment="拉取时指定的参数")

    def pull_fail(self, project, desc=None):
        """ 拉取失败 """
        self.model_update({"status": 0, "desc": self.dumps(desc)})
        project.last_pull_is_fail()

    def pull_success(self, project):
        """ 拉取成功 """
        self.model_update({"status": 2})
        project.last_pull_is_success()
