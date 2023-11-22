# -*- coding: utf-8 -*-
from ...base_model import BaseProject, BaseProjectEnv, db, HeadersFiled


class ApiProject(BaseProject):
    """ 服务表 """
    __abstract__ = False
    __tablename__ = "api_test_project"
    __table_args__ = {"comment": "接口测试服务表"}

    swagger = db.Column(db.String(255), default="", comment="服务对应的swagger地址")
    last_pull_status = db.Column(db.Integer(), default=1, comment="最近一次swagger拉取状态，0拉取失败，1未拉取，2拉取成功")

    def last_pull_is_fail(self):
        """ 最近一次从swagger拉取失败 """
        self.model_update({"last_pull_status": 0})

    def last_pull_is_success(self):
        """ 最近一次从swagger拉取成功 """
        self.model_update({"last_pull_status": 2})


class ApiProjectEnv(BaseProjectEnv, HeadersFiled):
    """ 服务环境表 """
    __abstract__ = False
    __tablename__ = "api_test_project_env"
    __table_args__ = {"comment": "接口测试服务环境表"}
