# -*- coding: utf-8 -*-
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseProject, BaseProjectEnv


class AppUiProject(BaseProject):
    """ app表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_project"
    __table_args__ = {"comment": "APP测试APP表"}

    app_package: Mapped[str] = mapped_column(String(255), nullable=False, comment="被测app包名")
    app_activity: Mapped[str] = mapped_column(String(255), nullable=False, comment="被测app要启动的AndroidActivity")
    template_device: Mapped[int] = mapped_column(Integer(), nullable=False, comment="元素定位时参照的设备")


class AppUiProjectEnv(BaseProjectEnv):
    """ app环境表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_project_env"
    __table_args__ = {"comment": "APP测试APP环境表"}
