# -*- coding: utf-8 -*-
import validators
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

from app.baseForm import BaseForm
from app.app_ui_test.models.env import AppUiRunServer as Server, AppUiRunPhone as Phone


class HasServerIdForm(BaseForm):
    """ 校验服务器id已存在 """
    id = IntegerField(validators=[DataRequired("服务器id必传")])

    def validate_id(self, field):
        """ 校验id存在 """
        server = self.validate_data_is_exist(f"任务id【{field.data}】不存在", Server, id=field.data)
        setattr(self, "server", server)


class AddServerForm(BaseForm):
    """ 添加服务器的校验 """

    name = StringField(validators=[DataRequired("服务器名字不能为空")])
    os = StringField(validators=[DataRequired("服务器系统类型不能为空")])
    ip = StringField(validators=[DataRequired("服务器ip地址不能为空")])
    port = StringField(validators=[DataRequired("服务器端口不能为空")])
    num = StringField()

    def validate_ip(self, field):
        """ 校验ip格式 """
        self.validate_data_is_true("服务器ip地址错误", validators.ipv4(field.data) or validators.ipv6(field.data))

    def validate_name(self, field):
        """ 校验服务器名不重复 """
        self.validate_data_is_not_exist(f"服务器名【{field.data}】已存在", Server, name=field.data)


class EditServerForm(HasServerIdForm, AddServerForm):
    """ 修改服务器的校验 """

    def validate_name(self, field):
        """ 校验服务器名不重复 """
        self.validate_data_is_not_repeat(
            f"服务器名【{field.data}】已存在",
            Server,
            self.id.data,
            name=field.data
        )


class GetServerListForm(BaseForm):
    """ 查找服务器信息 """
    name = StringField()
    os = StringField()
    ip = StringField()
    port = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class HasPhoneIdForm(BaseForm):
    """ 校验手机id已存在 """
    id = IntegerField(validators=[DataRequired("手机id必传")])

    def validate_id(self, field):
        """ 校验id存在 """
        phone = self.validate_data_is_exist(f"任务id【{field.data}】不存在", Phone, id=field.data)
        setattr(self, "phone", phone)


class AddPhoneForm(BaseForm):
    """ 添加手机的校验 """

    name = StringField(validators=[DataRequired("手机设备名字不能为空")])
    os = StringField(validators=[DataRequired("手机设备系统类型不能为空")])
    os_version = StringField(validators=[DataRequired("手机设备系统版本不能为空")])
    num = StringField()

    def validate_name(self, field):
        """ 校验手机名不重复 """
        self.validate_data_is_not_exist(f"手机设备名【{field.data}】已存在", Phone, name=field.data)


class EditPhoneForm(HasPhoneIdForm, AddPhoneForm):
    """ 修改手机的校验 """

    def validate_name(self, field):
        """ 校验手机名不重复 """
        self.validate_data_is_not_repeat(
            f"手机设备名【{field.data}】已存在",
            Phone,
            self.id.data,
            name=field.data
        )


class GetPhoneListForm(BaseForm):
    """ 查找服务器信息 """
    name = StringField()
    os = StringField()
    os_version = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()
