# -*- coding: utf-8 -*-
from flask_login import current_user

from app.baseModel import BaseModel, db


class ApiProject(BaseModel):
    """ 服务表 """
    __tablename__ = 'api_test_project'

    name = db.Column(db.String(255), nullable=True, comment='服务名称')
    manager = db.Column(db.Integer(), nullable=True, default=1, comment='服务管理员id，默认为admin')
    test = db.Column(db.String(255), default='', comment='测试环境域名')
    swagger = db.Column(db.String(255), default='', comment='服务对应的swagger地址')
    yapi_id = db.Column(db.Integer(), default=None, comment='对应YapiProject表里面的原始数据在yapi平台的id')

    def is_not_manager(self):
        """ 判断用户非服务负责人 """
        return current_user.id != self.manager

    @classmethod
    def is_not_manager_id(cls, project_id):
        """ 判断当前用户非当前数据的负责人 """
        return cls.get_first(id=project_id).manager != current_user.id

    @classmethod
    def is_manager_id(cls, project_id):
        """ 判断当前用户为当前数据的负责人 """
        return cls.get_first(id=project_id).manager == current_user.id

    @classmethod
    def is_admin(cls):
        """ 角色为2，为管理员 """
        return current_user.role_id == 2

    @classmethod
    def is_not_admin(cls):
        """ 角色不为2，非管理员 """
        return not cls.is_admin()

    @classmethod
    def is_can_delete(cls, project_id, obj):
        """
        判断是否有权限删除，
        可删除条件（或）：
        1.当前用户为系统管理员
        2.当前用户为当前数据的创建者
        3.当前用户为当前要删除服务的负责人
        """
        return ApiProject.is_manager_id(project_id) or cls.is_admin() or obj.is_create_user(current_user.id)

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.name.data:
            filters.append(ApiProject.name.like(f'%{form.name.data}%'))
        if form.projectId.data:
            filters.append(ApiProject.id == form.projectId.data)
        if form.manager.data:
            filters.append(ApiProject.manager == form.manager.data)
        if form.create_user.data:
            filters.append(ApiProject.create_user == form.create_user.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc())

    def create_env(self, env_list=None):
        if env_list is None:
            env_list = ['dev', 'test', 'uat', 'production']
        for env in env_list:
            ApiProjectEnv().create({"env": env, "project_id": self.id})


class ApiProjectEnv(BaseModel):
    """ 服务环境表 """
    __tablename__ = 'api_test_project_env'

    env = db.Column(db.String(10), nullable=True, comment='所属环境')
    host = db.Column(db.String(255), default='', comment='域名')
    func_files = db.Column(db.Text(), nullable=True, default='[]', comment='引用的函数文件')
    variables = db.Column(db.Text(), default='[{"key": "", "value": "", "remark": ""}]', comment='服务的公共变量')
    headers = db.Column(db.Text(), default='[{"key": "", "value": "", "remark": ""}]', comment='服务的公共头部信息')
    project_id = db.Column(db.Integer(), nullable=True, comment='所属的服务id')

    def to_dict(self, *args, **kwargs):
        """ 自定义序列化器，把模型的每个字段转为字典，方便返回给前端 """
        return super(ApiProjectEnv, self).to_dict(to_dict=["variables", "headers", "func_files"])
