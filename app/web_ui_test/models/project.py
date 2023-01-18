# -*- coding: utf-8 -*-
from app.baseModel import BaseProject, BaseProjectEnv, db
from app.config.models.runEnv import RunEnv


class WebUiProject(BaseProject):
    """ 服务表 """
    __abstract__ = False

    __tablename__ = "web_ui_test_project"

    use_host = db.Column(
        db.String(255), default="env", comment="运行时使用的域名，env: 环境设置的域名，project: 服务设置的域名"
    )
    service_addr = db.Column(db.String(16), default="", comment="服务地址，不含域名")

    def delete_current_and_env(self):
        """ 删除服务及服务下的环境 """
        return self.delete_current_and_children(WebUiProjectEnv, "project_id")


class WebUiProjectEnv(BaseProjectEnv):
    """ 服务环境表 """
    __abstract__ = False

    __tablename__ = "web_ui_test_project_env"

    env_service_addr = db.Column(db.String(225), default="", comment="服务地址，不含域名")
    use_service = db.Column(
        db.String(16), default="project", comment="运行时使用的服务地址，env: 环境设置的服务地址，project: 服务设置的服务地址"
    )

    @classmethod
    def create_env(cls, project_id=None, project_service_addr=None, env_list=None):
        """
        当环境配置更新时，自动给项目/环境增加环境信息
        如果指定了项目id，则只更新该项目的id，否则更新所有项目的id
        如果已有当前项目的信息，则用该信息创建到指定的环境
        """
        if not project_id and not env_list:
            return

        env_id_list = env_list or RunEnv.get_id_list('webUi')

        if project_id:
            current_project_env = cls.get_first(project_id=project_id)
            if current_project_env:
                data = current_project_env.to_dict()
            else:
                data = {"project_id": project_id, "env_service_addr": project_service_addr}

            for env_id in env_id_list:
                data["env_id"] = env_id
                cls().create(data)
        else:
            all_project = WebUiProject.get_all()
            for project in all_project:
                cls.create_env(project.id, project.service_addr, env_id_list)
