# -*- coding: utf-8 -*-

from app.baseModel import BaseProject, BaseProjectEnv, db
from app.config.models import Config


class ApiProject(BaseProject):
    """ 服务表 """
    __abstract__ = False

    __tablename__ = 'api_test_project'

    swagger = db.Column(db.String(255), default='', comment='服务对应的swagger地址')
    yapi_id = db.Column(db.Integer(), default=None, comment='对应YapiProject表里面的原始数据在yapi平台的id')


class ApiProjectEnv(BaseProjectEnv):
    """ 服务环境表 """
    __abstract__ = False

    __tablename__ = 'api_test_project_env'

    @classmethod
    def create_env(cls, project_id, env_list=None):
        """ 根据配置的环境列表设置环境 """
        env_list = env_list or cls.loads(Config.get_first(name='run_test_env').value).keys()
        for env in env_list:
            cls().create({"env": env, "project_id": project_id})
