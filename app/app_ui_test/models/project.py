# -*- coding: utf-8 -*-
from app.baseModel import BaseProject, BaseProjectEnv, db
from app.config.models.runEnv import RunEnv


class AppUiProject(BaseProject):
    """ app表 """
    __abstract__ = False

    __tablename__ = "app_ui_test_project"

    app_package = db.Column(db.String(255), nullable=True, comment="被测app包名")
    app_activity = db.Column(db.String(255), nullable=True, comment="被测app要启动的AndroidActivity")

    def delete_current_and_env(self):
        """ 删除app及app下的环境 """
        return self.delete_current_and_children(AppUiProjectEnv, "project_id")


class AppUiProjectEnv(BaseProjectEnv):
    """ app环境表 """
    __abstract__ = False

    __tablename__ = "app_ui_test_project_env"

    @classmethod
    def create_env(cls, project_id=None, env_list=None):
        """ 自动创建环境 """
        if not project_id and not env_list:
            return

        cls().create({"project_id": project_id})
