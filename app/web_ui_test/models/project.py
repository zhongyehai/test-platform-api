# -*- coding: utf-8 -*-

from app.baseModel import BaseProject, BaseProjectEnv, db
from app.config.models.config import Config


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

    cookies = db.Column(db.Text(), default='[{"key": "", "value": "", "remark": ""}]', comment='cookie')
    session_storage = db.Column(db.Text(), default='[{"key": "", "value": "", "remark": ""}]',
                                comment='session_storage')
    local_storage = db.Column(db.Text(), default='[{"key": "", "value": "", "remark": ""}]', comment='local_storage')

    @classmethod
    def create_env(cls, project_id, env_list=None):
        """ 根据配置的环境列表设置环境 """
        env_list = env_list or Config.get_run_test_env().keys()
        for env in env_list:
            cls().create({"env": env, "project_id": project_id})
