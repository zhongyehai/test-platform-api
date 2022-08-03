# -*- coding: utf-8 -*-

from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

from app.baseForm import BaseForm
from ..models.account import AccountModel


class GetAccountListForm(BaseForm):
    """ 获取账号列表 """
    page_num = IntegerField()
    page_size = IntegerField()
    event = StringField()
    project = StringField()
    name = StringField()


class GetAccountForm(BaseForm):
    """ 账号详情 """
    id = IntegerField(validators=[DataRequired('账号id必传')])

    def validate_id(self, field):
        account = self.validate_data_is_exist(f'id为 {field.data} 的账号不存在', AccountModel, id=field.data)
        setattr(self, 'account', account)


class DeleteAccountForm(GetAccountForm):
    """ 删除账号 """


class AddAccountForm(BaseForm):
    """ 添加账号 """
    project = StringField(validators=[DataRequired('请输入或选择服务名')])
    name = StringField(validators=[DataRequired('请输入账户名称')])
    account = StringField(validators=[DataRequired('请输入登录账号')])
    password = StringField(validators=[DataRequired('请输入登录密码')])
    event = StringField(validators=[DataRequired('请输入环境')])
    desc = StringField()

    def validate_account(self, field):
        """ 校验账号不重复 """
        self.validate_data_is_not_exist(
            f'当前环境下，账号【{field.data}】已存在，直接修改即可',
            AccountModel,
            project=self.project.data,
            event=self.event.data,
            account=self.account.data,
        )


class ChangeAccountForm(GetAccountForm, AddAccountForm):
    """ 修改账号 """

    def validate_account(self, field):
        """ 校验账号不重复 """
        self.validate_data_is_not_repeat(
            f'当前环境下，账号【{field.data}】已存在，直接修改即可',
            AccountModel,
            self.account.id,
            project=self.project.data,
            event=self.event.data,
            account=field.data,
        )
