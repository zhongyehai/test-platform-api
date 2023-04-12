# -*- coding: utf-8 -*-
from flask import g
from wtforms import StringField, IntegerField
from wtforms.validators import Length, DataRequired

from app.baseForm import BaseForm
from app.system.models.user import User, Role


class CreateUserForm(BaseForm):
    """ 创建用户的验证 """
    name = StringField(validators=[DataRequired("请设置用户名"), Length(2, 12, message="用户名长度为2~12位")])
    account = StringField(validators=[DataRequired("请设置账号"), Length(2, 50, message="账号长度为2~50位")])
    password = StringField(validators=[DataRequired("请设置密码"), Length(4, 18, message="密码长度长度为4~18位")])
    business_id = StringField(validators=[DataRequired("请选择业务线")])
    role_list = StringField(validators=[DataRequired("请选择角色")])

    def validate_name(self, field):
        """ 校验用户名不重复 """
        self.validate_data_is_not_exist(f"用户名 {field.data} 已存在", User, name=field.data)

    def validate_account(self, field):
        """ 校验账号不重复 """
        self.validate_data_is_not_exist(f"账号 {field.data} 已存在", User, account=field.data)


class ChangePasswordForm(BaseForm):
    """ 修改密码的校验 """
    oldPassword = StringField(validators=[Length(4, 18, message="密码长度长度为6~18位")])
    newPassword = StringField(validators=[Length(4, 18, message="密码长度长度为6~18位")])
    surePassword = StringField(validators=[Length(4, 18, message="密码长度长度为6~18位")])

    def validate_oldPassword(self, field):
        """ 校验旧密码是否正确 """
        user = User.get_first(id=g.user_id)
        self.validate_data_is_true(f"旧密码 {field.data} 错误", user.verify_password(field.data))
        setattr(self, "user", user)

    def validate_surePassword(self, field):
        """ 校验两次密码是否一致 """
        self.validate_data_is_true("新密码与确认密码不一致", self.newPassword.data == field.data)


class LoginForm(BaseForm):
    """ 登录校验 """
    account = StringField(validators=[DataRequired("账号必填")])
    password = StringField(validators=[DataRequired("密码必填")])

    def validate_account(self, field):
        """ 校验账号 """
        user = self.validate_data_is_exist("账号或密码错误", User, account=field.data)
        self.validate_data_is_true("账号或密码错误", user.verify_password(self.password.data))
        self.validate_data_is_true(f"账号 {field.data} 为冻结状态，请联系管理员", user.status != 0)
        setattr(self, "user", user)


class FindUserForm(BaseForm):
    """ 查找用户参数校验 """
    name = StringField()
    account = StringField()
    detail = StringField()
    status = IntegerField()
    role_id = IntegerField()
    pageNum = IntegerField()
    pageSize = IntegerField()

    def validate_detail(self, field):
        """ 如果要获取详情，需有管理员权限 """
        if field.data:
            self.validate_data_is_true("当前角色无权限", self.is_admin())


class GetUserForm(BaseForm):
    """ 返回待编辑用户信息 """
    id = IntegerField(validators=[DataRequired("用户id必传")])

    def validate_id(self, field):
        user = self.validate_data_is_exist(f"没有id为 {field.data} 的用户", User, id=field.data)
        setattr(self, "user", user)


class DeleteUserForm(GetUserForm):
    """ 删除用户 """

    def validate_id(self, field):
        user = self.validate_data_is_exist(f"没有id为 {field.data} 的用户", User, id=field.data)
        self.validate_data_is_false("不能自己删自己", user.id == g.user_id)
        setattr(self, "user", user)


class ChangeStatusUserForm(GetUserForm):
    """ 改变用户状态 """

    def validate_id(self, field):
        user = self.validate_data_is_exist(f"没有id为 {field.data} 的用户", User, id=field.data)
        setattr(self, "user", user)


class EditUserForm(GetUserForm, CreateUserForm):
    """ 编辑用户的校验 """
    password = StringField()

    def validate_id(self, field):
        """ 校验id需存在 """
        user = self.validate_data_is_exist(f"没有id为 {field.data} 的用户", User, id=field.data)
        setattr(self, "user", user)

    def validate_name(self, field):
        """ 校验用户名不重复 """
        self.validate_data_is_not_repeat(
            f"用户名 {field.data} 已存在",
            User,
            self.id.data,
            name=field.data
        )

    def validate_account(self, field):
        """ 校验账号不重复 """
        self.validate_data_is_not_repeat(
            f"账号 {field.data} 已存在",
            User,
            self.id.data,
            account=field.data
        )

    def validate_password(self, field):
        """ 如果密码字段没有值，则去掉此属性 """
        if not field.data:
            delattr(self, "password")
