# -*- coding: utf-8 -*-
from typing import Optional

from flask import request, g
from pydantic import Field, field_validator, ValidationInfo

from ...base_form import BaseForm, PaginationForm
from ..model_factory import User
from ...enums import DataStatusEnum


class GetUserListForm(PaginationForm):
    """ 查找用户参数校验 """
    name: Optional[str] = Field(None, title="用户名")
    account: Optional[str] = Field(None, title="账号")
    detail: Optional[str] = Field(False, title="是否获取用户详情")
    status: Optional[DataStatusEnum] = Field(None, title="状态")
    role_id: Optional[int] = Field(None, title="角色id")

    @field_validator("detail")
    def validate_detail(cls, value):
        if value:
            cls.validate_is_true(User.is_admin() or request.path in g.api_permissions, "当前角色无权限")
        return value

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []

        if User.is_not_admin():  # 非管理员，只能获取到当前用户有的业务线的人
            user_id_list = []
            for business_id in g.business_list:
                # 业务线可能包含指定业务线id的用户
                user_query_list = User.db.session.query(
                    User.id, User.business_list).filter(User.business_list.like(f"%{business_id}%")).all()
                for user_query in user_query_list:
                    if business_id in user_query[1]:  # 精确包含指定业务线id的用户
                        user_id_list.append(user_query[0])
            filter_list.append(User.id.in_(list(set(user_id_list))))
        if self.name:
            filter_list.append(User.name.like(f'%{self.name}%'))
        if self.account:
            filter_list.append(User.account == self.account)
        if self.status:
            filter_list.append(User.status == self.status)
        if self.role_id:
            filter_list.append(User.role_id == self.role_id)
        return filter_list


class GetUserForm(BaseForm):
    """ 获取用户信息 """
    id: int = Field(..., title="用户id")

    @field_validator("id")
    def validate_id(cls, value):
        user = cls.validate_data_is_exist("数据不存在", User, id=value)
        setattr(cls, "user", user)
        return value


class DeleteUserForm(GetUserForm):
    """ 删除用户 """

    @field_validator("id")
    def validate_id(cls, value):
        cls.validate_is_false(value == g.user_id, "不能自己删自己")
        return value


class ChangeStatusUserForm(GetUserForm):
    """ 改变用户状态 """


class ChangePasswordForm(BaseForm):
    """ 修改密码的校验 """
    old_password: str = Field(..., title="旧密码")
    new_password: str = Field(..., title="新密码")
    sure_password: str = Field(..., title="确认密码")

    @field_validator("new_password")
    def validate_new_password(cls, value, info: ValidationInfo):
        cls.validate_is_true(info.data["old_password"] == value, "新密码与确认密码不一致")
        return value

    @field_validator("old_password")
    def validate_old_password(cls, value):
        """ 校验旧密码是否正确 """
        user = User.get_first(id=g.user_id)
        cls.validate_is_true(user.verify_password(value), "旧密码错误")
        setattr(cls, "user", user)
        return value


class LoginForm(BaseForm):
    """ 登录校验 """
    account: str = Field(..., title="账号")
    password: str = Field(..., title="密码")

    @field_validator("account")
    def validate_account(cls, value):
        """ 校验账号 """
        user = cls.validate_data_is_exist("账号或密码错误", User, account=value)
        cls.validate_is_true(user.status != 0, "账号为冻结状态，请联系管理员")
        setattr(cls, "user", user)
        return value

    @field_validator("password")
    def validate_password(cls, value):
        cls.validate_is_true(getattr(cls, "user").verify_password(value), "账号或密码错误")
        return value


class CreateUserForm(BaseForm):
    """ 创建用户的验证 """
    user_list: list = Field(..., title="用户列表")

    @field_validator("user_list")
    def validate_user_list(cls, value):
        """ 校验用户数据 """
        name_list, account_list = [], []
        for index, user in enumerate(value):
            name, account, password = user.get("name"), user.get("account"), user.get("password")
            business_list, role_list = user.get("business_list"), user.get("role_list")
            if not all((name, account, password, business_list, role_list)):
                raise ValueError(f'第【{index + 1}】行，数据需填完')

            cls.validate_is_true(3 < len(password) < 50, f'第【{index + 1}】行，密码长度长度为4~50位')

            if name in name_list:
                raise ValueError(f'第【{index + 1}】行，与第【{name_list.index(name) + 1}】行，用户名重复')
            cls.validate_is_true(1 < len(name) < 12, f'第【{index + 1}】行，用户名长度长度为2~12位')
            cls.validate_data_is_not_exist(f'【第{index + 1}】行，用户名【{name}】已存在', User, name=name)

            if account in account_list:
                raise ValueError(f'第【{index + 1}】行，与第【{account_list.index(account) + 1}】行，账号重复')
            cls.validate_is_true(1 < len(account) < 50, f'第【{index + 1}】行，账号长度长度为2~50位')
            cls.validate_data_is_not_exist(f'第【{index + 1}】行，账号【{account}】已存在', User, account=account)

            name_list.append(name)
            account_list.append(account)
            return value


class EditUserForm(GetUserForm):
    """ 编辑用户的校验 """
    name: str = Field(..., title="用户名")
    account: str = Field(..., title="账号")
    business_list: list = Field(..., title="业务线")
    role_list: list = Field(..., title="角色")
    # password: Optional[str] = Field(None, title="用户密码，如果有，则可直接修改密码")
