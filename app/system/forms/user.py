# -*- coding: utf-8 -*-
from flask import g
from wtforms import StringField, IntegerField
from wtforms.validators import Length, DataRequired, ValidationError

from app.baseForm import BaseForm
from app.system.models.user import User


class CreateUserForm(BaseForm):
    """ 创建用户的验证 """
    user_list = StringField(validators=[DataRequired("用户信息必传")])

    def validate_user_list(self, field):
        """ 校验用户数据 """
        name_list, account_list = [], []
        for index, user in enumerate(field.data):
            name, account, password = user.get("name"), user.get("account"), user.get("password")
            business_list, role_list = user.get("business_list"), user.get("role_list")
            if not all((name, account, password, business_list, role_list)):
                raise ValidationError(f'第【{index + 1}】行，数据需填完')

            self.validate_data_is_true(f'第【{index + 1}】行，密码长度长度为4~50位', 3 < len(password) < 50)

            if name in name_list:
                raise ValidationError(f'第【{index + 1}】行，与第【{name_list.index(name) + 1}】行，用户名重复')
            self.validate_data_is_true(f'第【{index + 1}】行，用户名长度长度为2~12位', 1 < len(name) < 12)
            self.validate_data_is_not_exist(f'【第{index + 1}】行，用户名【{name}】已存在', User, name=name)

            if account in account_list:
                raise ValidationError(f'第【{index + 1}】行，与第【{account_list.index(account) + 1}】行，账号重复')
            self.validate_data_is_true(f'第【{index + 1}】行，账号长度长度为2~50位', 1 < len(account) < 50)
            self.validate_data_is_not_exist(f'第【{index + 1}】行，账号【{account}】已存在', User, account=account)

            name_list.append(name)
            account_list.append(account)


class ChangePasswordForm(BaseForm):
    """ 修改密码的校验 """
    oldPassword = StringField(validators=[Length(4, 50, message="密码长度长度为4~50位")])
    newPassword = StringField(validators=[Length(4, 50, message="密码长度长度为4~50位")])
    surePassword = StringField(validators=[Length(4, 50, message="密码长度长度为4~50位")])

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
    """ 获取用户信息 """
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


class EditUserForm(GetUserForm):
    """ 编辑用户的校验 """
    name = StringField(validators=[DataRequired("请设置用户名"), Length(2, 12, message="用户名长度为2~12位")])
    account = StringField(validators=[DataRequired("请设置账号"), Length(2, 50, message="账号长度为2~50位")])
    password = StringField()
    business_list = StringField(validators=[DataRequired("请选择业务线")])
    role_list = StringField(validators=[DataRequired("请选择角色")])

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
        if field.data:
            self.validate_data_is_true('密码长度长度为4~50位', 3 < len(field.data) < 51)
