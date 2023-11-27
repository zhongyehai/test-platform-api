# -*- coding: utf-8 -*-
from datetime import datetime

from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
from flask import current_app as app

from apps.base_model import BaseModel, NumFiled


class Permission(NumFiled):
    """ 权限表 """
    __tablename__ = "system_permission"
    __table_args__ = {"comment": "权限表"}

    name: Mapped[str] = mapped_column(String(30), unique=True, comment="权限名称")
    desc: Mapped[str] = mapped_column(String(256), nullable=True, comment="权限备注")
    source_addr: Mapped[str] = mapped_column(String(256), comment="权限路径")
    source_type: Mapped[str] = mapped_column(String(256), default="api", comment="权限类型， front前端, api后端")
    source_class: Mapped[str] = mapped_column(
        String(256), default="api",
        comment="权限分类, source_type为front时, menu菜单, button按钮;  source_type为api时, 为请求方法")

    @classmethod
    def get_role_permissions(cls, role_id):
        """ 根据角色id获取对应的权限id """
        role_id_list = []
        Role.get_all_role_id(role_id, role_id_list)
        role_permissions = [data.permission_id for data in RolePermissions.get_all(role_id=role_id)]
        permissions = Permission.query.filter(Permission.id.in_(role_permissions)).all()
        all_permissions, front_permissions, api_permissions = [], [], []
        for permission in permissions:
            all_permissions.append(permission.id)
            if permission.source_type == 'api':
                api_permissions.append(permission.id)
            else:
                front_permissions.append(permission.id)
        return {
            "all_permissions": all_permissions,
            "front_permissions": front_permissions,
            "api_permissions": api_permissions
        }

    @classmethod
    def get_addr_list(cls, permission_id_list, source_type='front'):
        """ 根据权限id获取权限地址列表 """
        source_list = cls.query.filter(cls.id.in_(permission_id_list), cls.source_type == source_type).all()
        return [source.source_addr for source in source_list]


class Role(BaseModel):
    """ 角色表 """
    __tablename__ = "system_role"
    __table_args__ = {"comment": "角色表"}

    name: Mapped[str] = mapped_column(String(30), unique=True, comment="角色名称")
    extend_role: Mapped[list] = mapped_column(JSON, default=[], comment="继承其他角色的权限")
    desc: Mapped[str] = mapped_column(String(256), comment="权限备注")

    @classmethod
    def get_all_role_id(cls, role_id, id_list=[]):
        """ 递归获取角色拥有的角色（可能存在继承关系） """
        role = cls.get_first(id=role_id)
        id_list.append(role.id)
        extend_role_id_list = role.extend_role
        if extend_role_id_list:
            for role_id in extend_role_id_list:
                cls.get_all_role_id(role_id, id_list)
        return id_list

    def insert_role_permissions(self, permission_id_list):
        """ 插入角色权限映射 """
        for permission_id in permission_id_list:
            RolePermissions.model_create({"role_id": self.id, "permission_id": permission_id})

    @classmethod
    def get_user_role_list(cls, user_id):
        """ 获取用户的角色 """
        id_list = []
        query_list = UserRoles.query.with_entities(UserRoles.role_id).filter(UserRoles.user_id == user_id).all()
        role_id_list = cls.format_with_entities_query_list(query_list)

        for role_id in role_id_list:
            cls.get_extend_role(role_id, id_list)

        return id_list

    @classmethod
    def get_extend_role(cls, role_id, id_list=[]):
        """ 获取继承的角色的id """
        id_list.append(role_id)
        extend_role_list = Role.query.with_entities(Role.extend_role).filter(Role.id == role_id).first()  # ([],)
        for role_id in extend_role_list[0]:
            cls.get_extend_role(role_id, id_list)
        return id_list

    def delete_role_permissions(self):
        """ 根据角色删除权限映射 """
        with RolePermissions.db.auto_commit():
            RolePermissions.query.filter(RolePermissions.role_id == self.id).delete()

    def update_role_permissions(self, permission_id_list):
        """ 更新角色权限映射 """
        self.delete_role_permissions()
        self.insert_role_permissions(permission_id_list)


class RolePermissions(BaseModel):
    """ 角色权限映射表 """
    __tablename__ = "system_role_permissions"
    __table_args__ = {"comment": "角色权限映射表"}

    role_id: Mapped[int] = mapped_column(Integer(), comment="角色id")
    permission_id: Mapped[int] = mapped_column(Integer(), comment="权限id")


class User(BaseModel):
    """ 用户表 """
    __tablename__ = "system_user"
    __table_args__ = {"comment": "用户表"}

    sso_user_id: Mapped[str] = mapped_column(String(50), index=True, nullable=True, comment="该用户在oss数据库的账号")
    account: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment="账号")
    password_hash: Mapped[str] = mapped_column(String(255), comment="密码")
    name: Mapped[str] = mapped_column(String(12), comment="姓名")
    status: Mapped[int] = mapped_column(Integer(), default=1, comment="状态，1为启用，0为冻结")
    business_list: Mapped[str] = mapped_column(JSON, default=[], comment="用户拥有的业务线")

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, _password):
        """ 设置加密密码 """
        self.password_hash = generate_password_hash(_password)

    def verify_password(self, password):
        """ 校验密码 """
        return check_password_hash(self.password_hash, password)

    def make_token(self, api_permissions: list = []):
        """ 生成token，默认有效期为系统配置的时长 """
        user_info = {
            "id": self.id,
            "name": self.name,
            "role_list": self.roles,
            "api_permissions": api_permissions,
            "business_list": self.business_list,
            "exp": datetime.now().timestamp() + app.config["TOKEN_TIME_OUT"]
        }
        return jwt.encode(user_info, app.config["SECRET_KEY"])

    @property
    def roles(self):
        """ 获取用户的角色id """
        return [user_role.role_id for user_role in UserRoles.get_all(user_id=self.id)]

    def get_permissions(self):
        """ 获取用户的前端权限 """
        role_id_list = Role.get_user_role_list(self.id)

        # 所有权限的id
        all_permission_id_list = RolePermissions.query.with_entities(
            RolePermissions.permission_id).filter(RolePermissions.role_id.in_(role_id_list)).distinct().all()
        permission_id_list = list(self.format_with_entities_query_list(all_permission_id_list))

        # 所有前端权限
        all_front_addr_list = Permission.query.with_entities(Permission.source_addr).filter(
            Permission.id.in_(permission_id_list), Permission.source_type == 'front').distinct().all()
        front_addr_list = list(self.format_with_entities_query_list(all_front_addr_list))

        # 所有后端权限
        all_api_addr_list = Permission.query.with_entities(Permission.source_addr).filter(
            Permission.id.in_(permission_id_list), Permission.source_type == 'api').distinct().all()
        api_addr_list = list(self.format_with_entities_query_list(all_api_addr_list))

        return {"front_addr_list": front_addr_list, "api_addr_list": api_addr_list}

    def insert_user_roles(self, role_id_list):
        """ 插入用户角色映射 """
        for role_id in role_id_list:
            UserRoles.model_create({"user_id": self.id, "role_id": role_id})

    def delete_user_roles(self):
        """ 根据用户删除角色映射 """
        for user_role in UserRoles.get_all(user_id=self.id):
            user_role.delete()

    def update_user_roles(self, role_id_list):
        """ 更新用户角色映射 """
        self.delete_user_roles()
        self.insert_user_roles(role_id_list)

    def to_dict(self, *args, **kwargs):
        return super(User, self).to_dict(pop_list=["password_hash"], filter_list=kwargs.get("filter_list", []))


class UserRoles(BaseModel):
    """ 用户角色映射表 """
    __tablename__ = "system_user_roles"
    __table_args__ = {"comment": "用户角色映射表"}

    user_id: Mapped[str] = mapped_column(Integer(), comment="用户id")
    role_id: Mapped[str] = mapped_column(Integer(), comment="角色id")
