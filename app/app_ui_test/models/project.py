# -*- coding: utf-8 -*-
from app.baseModel import BaseProject, BaseProjectEnv, db
from app.config.models.runEnv import RunEnv


class AppUiProject(BaseProject):
    """ app表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_project"
    __table_args__ = {"comment": "APP测试APP表"}

    app_package = db.Column(db.String(255), nullable=True, comment="被测app包名")
    app_activity = db.Column(db.String(255), nullable=True, comment="被测app要启动的AndroidActivity")

    def delete_current_and_env(self):
        """ 删除app及app下的环境 """
        return self.delete_current_and_children(AppUiProjectEnv, "project_id")


class AppUiProjectEnv(BaseProjectEnv):
    """ app环境表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_project_env"
    __table_args__ = {"comment": "APP测试APP环境表"}

    @classmethod
    def create_env(cls, project_id=None, env_list=None):
        """
        当环境配置更新时，自动给项目/环境增加环境信息
        如果指定了项目id，则只更新该项目的id，否则更新所有项目的id
        如果已有当前项目的信息，则用该信息创建到指定的环境
        """
        if not project_id and not env_list:
            return

        env_id_list = env_list or RunEnv.get_id_list()

        if project_id:
            current_project_env = cls.get_first(project_id=project_id)
            if current_project_env:
                data = current_project_env.to_dict()
            else:
                data = {"project_id": project_id}

            for env_id in env_id_list:
                data["env_id"] = env_id
                cls().create(data)
        else:
            all_project = AppUiProject.get_all()
            for project in all_project:
                cls.create_env(project.id, env_id_list)
