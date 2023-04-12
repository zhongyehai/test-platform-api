# -*- coding: utf-8 -*-
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import check_password_hash, generate_password_hash

from flask import current_app as app

from app.baseModel import BaseModel, db


class Permission(BaseModel):
    """ 权限表 """
    __tablename__ = "system_permission"
    __table_args__ = {"comment": "权限表"}

    name = db.Column(db.String(30), comment="权限名称")
    desc = db.Column(db.String(256), comment="权限备注")
    num = db.Column(db.Integer(), nullable=True, comment="序号")
    source_addr = db.Column(db.String(256), comment="权限路径")
    source_type = db.Column(db.String(256), default="api", comment="权限类型， front前端, api后端")
    source_class = db.Column(db.String(256), default="api", comment="权限分类, source_type为front时, menu菜单, button按钮;  source_type为api时, 为请求方法")

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

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.name.data:
            filters.append(cls.name.like(f"%{form.name.data}%"))
        if form.source_addr.data:
            filters.append(cls.source_addr.like(f"%{form.name.data}%"))
        if form.source_type.data:
            filters.append(cls.source_type == form.source_type.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )


class Role(BaseModel):
    """ 角色表 """
    __tablename__ = "system_role"
    __table_args__ = {"comment": "角色表"}

    name = db.Column(db.String(30), unique=True, comment="角色名称")
    extend_role = db.Column(db.String(256), default='[]', comment="继承其他角色的权限")
    desc = db.Column(db.String(256), comment="权限备注")

    @classmethod
    def get_all_role_id(cls, role_id, id_list=[]):
        """ 递归获取角色拥有的角色（可能存在继承关系） """
        role = cls.get_first(id=role_id)
        id_list.append(role.id)
        extend_role_id_list = cls.loads(role.extend_role)
        if extend_role_id_list:
            for role_id in extend_role_id_list:
                cls.get_all_role_id(role_id, id_list)
        return id_list

    def insert_role_permissions(self, permission_id_list):
        """ 插入角色权限映射 """
        for permission_id in permission_id_list:
            RolePermissions().create({
                "role_id": self.id,
                "permission_id": permission_id
            })

    @classmethod
    def get_user_role_list(cls, user_id):
        """ 获取用户的角色 """
        role_id_list = [user_role.role_id for user_role in UserRoles.get_all(user_id=user_id)]
        return cls.query.filter(cls.id.in_(role_id_list)).all()

    def delete_role_permissions(self):
        """ 根据角色删除权限映射 """
        for role_permission in RolePermissions.get_all(role_id=self.id):
            role_permission.delete()

    def update_role_permissions(self, permission_id_list):
        """ 更新角色权限映射 """
        self.delete_role_permissions()
        self.insert_role_permissions(permission_id_list)

    def get_role_permissions_addr(self, source_type):
        """ 获取角色的权限地址 """
        role_id_list, addr_list = [], []
        self.get_all_role_id(self.id, role_id_list)
        for role_id in role_id_list:
            role_permissions = RolePermissions.get_all(role_id=role_id)
            for data in role_permissions:
                permission = Permission.get_first(id=data.permission_id, source_type=source_type)
                if permission:  # 区分前后端，可能查不到
                    addr_list.append(permission.source_addr)
        return addr_list

    def get_role_permissions_front_addr(self):
        """ 获取角色的前端权限地址 """
        return self.get_role_permissions_addr('front')

    def get_role_permissions_api_addr(self):
        """ 获取角色的后端权限地址 """
        return self.get_role_permissions_addr('api')

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.name.data:
            filters.append(cls.name.like(f"%{form.name.data}%"))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc())


class RolePermissions(BaseModel):
    """ 角色权限映射表 """
    __tablename__ = "system_role_permissions"
    __table_args__ = {"comment": "角色权限映射表"}

    role_id = db.Column(db.Integer, comment="角色id")
    permission_id = db.Column(db.Integer, comment="权限id")


class User(BaseModel):
    """ 用户表 """
    __tablename__ = "system_user"
    __table_args__ = {"comment": "用户表"}

    account = db.Column(db.String(50), unique=True, index=True, comment="账号")
    password_hash = db.Column(db.String(255), comment="密码")
    name = db.Column(db.String(12), comment="姓名")
    status = db.Column(db.Integer, default=1, comment="状态，1为启用，0为冻结")
    business_id = db.Column(db.String(255), comment="用户所在的业务线")

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

    def generate_reset_token(self, expiration=None):
        """ 生成token，默认有效期为系统配置的时长 """
        return Serializer(
            app.config["SECRET_KEY"],
            expiration or app.config["TOKEN_TIME_OUT"]
        ).dumps({
            "id": self.id,
            "name": self.name,
            "role_list": self.roles,
            "api_permissions": self.get_api_permissions(),
            "business_id": self.loads(self.business_id),
        }).decode("utf-8")

    @property
    def roles(self):
        """ 获取用户的角色id """
        return [user_role.role_id for user_role in UserRoles.get_all(user_id=self.id)]

    def get_front_permissions(self):
        """ 获取用户的前端权限 """
        permission_list = []
        for role in Role.get_user_role_list(self.id):
            permission_list.extend(role.get_role_permissions_front_addr())
        return list(set(permission_list))

    def get_api_permissions(self):
        """ 获取用户的后端权限 """
        permission_list = []
        for role in Role.get_user_role_list(self.id):
            permission_list.extend(role.get_role_permissions_api_addr())
        return list(set(permission_list))

    def insert_user_roles(self, role_id_list):
        """ 插入用户角色映射 """
        for role_id in role_id_list:
            UserRoles().create({"user_id": self.id, "role_id": role_id})

    def delete_user_roles(self):
        """ 根据用户删除角色映射 """
        for user_role in UserRoles.get_all(user_id=self.id):
            user_role.delete()

    def update_user_roles(self, role_id_list):
        """ 更新用户角色映射 """
        self.delete_user_roles()
        self.insert_user_roles(role_id_list)

    # @classmethod
    # def is_admin(cls, user_id=None):
    #     """返回当前用户是否为管理员权限 """
    #     return UserRoles.get_first(user_id=user_id or cls.id, role_id=Role.get_admin_id())
        # role_id = Role.get_admin_id()
        # if user_id:
        #     return cls.get_first(id=user_id).role_id == role_id
        # return cls.role == role_id

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.name.data:
            filters.append(User.name.like(f"%{form.name.data}%"))
        if form.account.data:
            filters.append(User.account.like(f"%{form.account.data}%"))
        if form.status.data:
            filters.append(User.status == form.status.data)
        if form.role_id.data:
            filters.append(User.role_id == form.role_id.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc())

    def to_dict(self, *args, **kwargs):
        return super(User, self).to_dict(pop_list=["password_hash"], filter_list=kwargs.get("filter_list", []))

    # def can(self, permission_name):
    #     """ 判断当前用户是否有当前请求的权限 """
    #     permission = Permission.query.filter_by(name=permission_name).first()
    #     return permission is not None and self.role is not None and permission in self.role.permission


class UserRoles(BaseModel):
    """ 用户角色映射表 """
    __tablename__ = "system_user_roles"
    __table_args__ = {"comment": "用户角色映射表"}

    user_id = db.Column(db.Integer, comment="用户id")
    role_id = db.Column(db.Integer, comment="角色id")
