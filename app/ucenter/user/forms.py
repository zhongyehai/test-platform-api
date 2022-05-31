# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:10
# @Author : ZhongYeHai
# @Site :
# @File : forms.py
# @Software: PyCharm
from flask_login import current_user
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, Length, DataRequired

from app.baseForm import BaseForm
from .models import User, Role


class CreateUserForm(BaseForm):
    """ 创建用户的验证 """
    name = StringField(validators=[DataRequired('请设置用户名'), Length(2, 12, message='用户名长度为2~12位')])
    account = StringField(validators=[DataRequired('请设置账号'), Length(2, 50, message='账号长度为2~50位')])
    password = StringField(validators=[DataRequired('请设置密码'), Length(6, 18, message='密码长度长度为6~18位')])
    role_id = IntegerField(validators=[DataRequired('请选择角色')])

    def validate_name(self, field):
        """ 校验用户名不重复 """
        if User.get_first(name=field.data):
            raise ValidationError(f'用户名 {field.data} 已存在')

    def validate_account(self, field):
        """ 校验账号不重复 """
        if User.get_first(account=field.data):
            raise ValidationError(f'账号 {field.data} 已存在')

    def validate_role_id(self, field):
        """ 校验角色存在 """
        if not Role.get_first(id=field.data):
            raise ValidationError(f'id为 {field.data} 的角色不存在')


class ChangePasswordForm(BaseForm):
    """ 修改密码的校验 """
    oldPassword = StringField(validators=[Length(6, 18, message='密码长度长度为6~18位')])
    newPassword = StringField(validators=[Length(6, 18, message='密码长度长度为6~18位')])
    surePassword = StringField(validators=[Length(6, 18, message='密码长度长度为6~18位')])

    def validate_oldPassword(self, field):
        """ 校验旧密码是否正确 """
        if not current_user.verify_password(field.data):
            raise ValidationError(f'旧密码 {field.data} 错误')

    def validate_surePassword(self, field):
        """ 校验两次密码是否一致 """
        if self.newPassword.data != field.data:
            raise ValidationError(f'新密码 {self.newPassword} 与确认密码 {field.data} 不一致')


class LoginForm(BaseForm):
    """ 登录校验 """
    account = StringField(validators=[DataRequired('账号必填')])
    password = StringField(validators=[DataRequired('密码必填')])

    def validate_account(self, field):
        """ 校验账号 """
        user = User.get_first(account=field.data)
        if user is None or not user.verify_password(self.password.data):
            raise ValidationError(f'账号或密码错误')
        if user.status == 0:
            raise ValidationError(f'账号 {field.data} 为冻结状态，请联系管理员')
        setattr(self, 'user', user)


class FindUserForm(BaseForm):
    """ 查找用户参数校验 """
    name = StringField()
    account = StringField()
    status = IntegerField()
    role_id = IntegerField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class GetUserEditForm(BaseForm):
    """ 返回待编辑用户信息 """
    id = IntegerField(validators=[DataRequired('用户id必传')])

    def validate_id(self, field):
        user = User.get_first(id=field.data)
        if not user:
            raise ValidationError(f'没有id为 {field.data} 的用户')
        setattr(self, 'user', user)


class DeleteUserForm(GetUserEditForm):
    """ 删除用户 """

    def validate_id(self, field):
        user = User.get_first(id=field.data)
        if not user:
            raise ValidationError(f'没有id为 {field.data} 的用户')
        if user.id == current_user.id:
            raise ValidationError('不能自己删自己')
        setattr(self, 'user', user)


class ChangeStatusUserForm(GetUserEditForm):
    """ 改变用户状态 """

    def validate_id(self, field):
        user = User.get_first(id=field.data)
        if not user:
            raise ValidationError(f'没有id为 {field.data} 的用户')
        setattr(self, 'user', user)


class EditUserForm(GetUserEditForm, CreateUserForm):
    """ 编辑用户的校验 """
    password = StringField()

    def validate_id(self, field):
        """ 校验id需存在 """
        user = User.get_first(id=field.data)
        if not user:
            raise ValidationError(f'id为 {field.data} 的用户不存在')
        setattr(self, 'user', user)

    def validate_name(self, field):
        """ 校验用户名不重复 """
        old_data = User.get_first(name=field.data)
        if old_data and old_data.name == field.data and old_data.id != self.id.data:
            raise ValidationError(f'用户名 {field.data} 已存在')

    def validate_account(self, field):
        """ 校验账号不重复 """
        old_data = User.get_first(account=field.data)
        if old_data and old_data.account == field.data and old_data.id != self.id.data:
            raise ValidationError(f'账号 {field.data} 已存在')
