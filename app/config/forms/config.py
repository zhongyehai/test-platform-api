# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

from app.config.models.config import Config, ConfigType
from app.baseForm import BaseForm


class GetConfigTypeListForm(BaseForm):
    """ 获取配置类型列表 """
    pageNum = IntegerField()
    pageSize = IntegerField()


class ConfigTypeIdForm(BaseForm):
    """ 配置类型id存在 """
    id = IntegerField(validators=[DataRequired('配置类型id必传')])

    def validate_id(self, field):
        conf_type = self.validate_data_is_exist(f'id为 {field.data} 的配置类型不存在', ConfigType, id=field.data)
        setattr(self, 'conf_type', conf_type)


class DeleteConfigTypeForm(ConfigTypeIdForm):
    """ 删除配置类型表单校验 """


class GetConfigTypeForm(DeleteConfigTypeForm):
    """ 获取配置类型表单校验 """


class PostConfigTypeForm(BaseForm):
    """ 新增配置类型表单校验 """
    name = StringField(validators=[DataRequired('请输入配置类型')])
    desc = StringField()

    def validate_name(self, field):
        self.validate_data_is_not_exist(f'名为 {field.data} 的配置类型已存在', ConfigType, name=field.data)


class PutConfigTypeForm(ConfigTypeIdForm, PostConfigTypeForm):
    """ 修改配置类型表单校验 """

    def validate_name(self, field):
        self.validate_data_is_not_repeat(
            f'名为 {field.data} 的配置类型已存在',
            ConfigType,
            self.id.data,
            name=field.data
        )


class GetConfigListForm(BaseForm):
    """ 获取配置列表 """
    type = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class ConfigIdForm(BaseForm):
    """ 配置id存在 """
    id = IntegerField(validators=[DataRequired('配置id必传')])

    def validate_id(self, field):
        conf = self.validate_data_is_exist(f'id为 {field.data} 的配置不存在', Config, id=field.data)
        setattr(self, 'conf', conf)


class DeleteConfigForm(ConfigIdForm):
    """ 删除配置表单校验 """


class GetConfigForm(DeleteConfigForm):
    """ 获取配置表单校验 """


class PostConfigForm(BaseForm):
    """ 新增配置表单校验 """
    name = StringField(validators=[DataRequired('请输入配置名')])
    value = StringField(validators=[DataRequired('请输入配置的值')])
    type = StringField(validators=[DataRequired('请输入配置的类型')])
    desc = StringField()

    def validate_name(self, field):
        self.validate_data_is_not_exist(f'名为 {field.data} 的配置已存在', Config, name=field.data)


class PutConfigForm(ConfigIdForm, PostConfigForm):
    """ 修改配置表单校验 """

    def validate_name(self, field):
        self.validate_data_is_not_repeat(
            f'名为 {field.data} 的配置已存在',
            Config,
            self.id.data,
            name=field.data
        )
