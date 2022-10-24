# -*- coding: utf-8 -*-

from app.baseModel import BaseProject, BaseProjectEnv, db, Config


class WebUiProject(BaseProject):
    """ 服务表 """
    __abstract__ = False

    __tablename__ = 'web_ui_test_project'

    def delete_current_and_env(self):
        """ 删除服务及服务下的环境 """
        return self.delete_current_and_children(WebUiProjectEnv, 'project_id')


class WebUiProjectEnv(BaseProjectEnv):
    """ 服务环境表 """
    __abstract__ = False

    __tablename__ = 'web_ui_test_project_env'

    @classmethod
    def create_env(cls, project_id=None, env_list=None):
        """
        当环境配置更新时，自动给项目/环境增加环境信息
        如果指定了项目id，则只更新该项目的id，否则更新所有项目的id
        如果已有当前项目的信息，则用该信息创建到指定的环境
        """
        if not project_id and not env_list:
            return

        env_list = env_list or Config.get_run_test_env().keys()

        if project_id:
            current_project_env = cls.get_first(project_id=project_id)
            data = current_project_env.to_dict() if current_project_env else {"project_id": project_id}

            for env in env_list:
                data["env"] = env
                cls().create(data)
        else:
            all_project = WebUiProject.get_all()
            for project in all_project:
                cls.create_env(project.id, env_list)
