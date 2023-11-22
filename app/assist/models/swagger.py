# -*- coding: utf-8 -*-
from app.base_model import BaseModel, db


class SwaggerPullLog(BaseModel):
    """ swagger拉取日志 """
    __tablename__ = "swagger_pull_log"
    __table_args__ = {"comment": "swagger拉取日志"}

    status = db.Column(db.Integer, default=1, comment="拉取结果，0失败，1拉取中，2拉取成功")
    project_id = db.Column(db.Integer, comment="服务id")
    desc = db.Column(db.Text, comment="备注")
    pull_args = db.Column(db.JSON, comment="拉取时指定的参数")

    def pull_fail(self, project, desc=None):
        """ 拉取失败 """
        self.model_update({"status": 0, "desc": self.dumps(desc)})
        project.last_pull_is_fail()

    def pull_success(self, project):
        """ 拉取成功 """
        self.model_update({"status": 2})
        project.last_pull_is_success()
