# -*- coding: utf-8 -*-

from app.baseModel import BaseProject, BaseProjectEnv, db
from app.config.models.config import Config


class ApiProject(BaseProject):
    """ 服务表 """
    __abstract__ = False

    __tablename__ = 'api_test_project'

    swagger = db.Column(db.String(255), default='', comment='服务对应的swagger地址')
    yapi_id = db.Column(db.Integer(), default=None, comment='对应YapiProject表里面的原始数据在yapi平台的id')

    def delete_current_and_env(self):
        """ 删除服务及服务下的环境 """
        return self.delete_current_and_children(ApiProjectEnv, 'project_id')


class ApiProjectEnv(BaseProjectEnv):
    """ 服务环境表 """
    __abstract__ = False

    __tablename__ = 'api_test_project_env'

    headers = db.Column(db.Text(), default='[{"key": "", "value": "", "remark": ""}]', comment='服务的公共头部信息')

    @classmethod
    def create_env(cls, project_id, env_list=None):
        """ 根据配置的环境列表设置环境 """
        env_list = env_list or Config.get_run_test_env().keys()
        for env in env_list:
            cls().create({"env": env, "project_id": project_id})
