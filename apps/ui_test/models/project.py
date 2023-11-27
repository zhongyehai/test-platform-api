# -*- coding: utf-8 -*-
from apps.base_model import BaseProject, BaseProjectEnv


class WebUiProject(BaseProject):
    """ 服务表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_project"
    __table_args__ = {"comment": "web-ui测试项目表"}


class WebUiProjectEnv(BaseProjectEnv):
    """ 服务环境表 """
    __abstract__ = False
    __tablename__ = "web_ui_test_project_env"
    __table_args__ = {"comment": "web-ui测试项目环境表"}
