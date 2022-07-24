# -*- coding: utf-8 -*-

from app.baseModel import BaseProject, BaseProjectEnv, db
from app.config.models.config import Config


class UiProject(BaseProject):
    """ 服务表 """
    __abstract__ = False

    __tablename__ = 'ui_test_project'


class UiProjectEnv(BaseProjectEnv):
    """ 服务环境表 """
    __abstract__ = False

    __tablename__ = 'ui_test_project_env'

    cookies = db.Column(db.Text(), default='[{"key": "", "value": "", "remark": ""}]', comment='cookie')
    session_storage = db.Column(db.Text(), default='[{"key": "", "value": "", "remark": ""}]', comment='session_storage')
    local_storage = db.Column(db.Text(), default='[{"key": "", "value": "", "remark": ""}]', comment='local_storage')

    @classmethod
    def create_env(cls, project_id, env_list=None):
        """ 根据配置的环境列表设置环境 """
        env_list = env_list or cls.loads(Config.get_first(name='run_test_env').value).keys()
        for env in env_list:
            cls().create({"env": env, "project_id": project_id})
