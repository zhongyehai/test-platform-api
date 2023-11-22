# -*- coding: utf-8 -*-
from app.base_model import BaseProject, BaseProjectEnv, db


class AppUiProject(BaseProject):
    """ app表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_project"
    __table_args__ = {"comment": "APP测试APP表"}

    app_package = db.Column(db.String(255), nullable=False, comment="被测app包名")
    app_activity = db.Column(db.String(255), nullable=False, comment="被测app要启动的AndroidActivity")
    template_device = db.Column(db.Integer(), nullable=False, comment="元素定位时参照的设备")


class AppUiProjectEnv(BaseProjectEnv):
    """ app环境表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_project_env"
    __table_args__ = {"comment": "APP测试APP环境表"}
