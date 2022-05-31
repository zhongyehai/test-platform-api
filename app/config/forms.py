# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired

from .models import Config, ConfigType
from app.baseForm import BaseForm


class GetConfigTypeListForm(BaseForm):
    """ 获取配置类型列表 """
    pageNum = IntegerField()
    pageSize = IntegerField()


class DeleteConfigTypeForm(BaseForm):
    """ 删除配置类型表单校验 """
    id = IntegerField(validators=[DataRequired('配置类型id必传')])

    def validate_id(self, field):
        conf_type = ConfigType.get_first(id=field.data)
        if not conf_type:
            raise ValidationError(f'id为 {field.data} 的配置类型不存在')
        setattr(self, 'conf_type', conf_type)


class GetConfigTypeForm(DeleteConfigTypeForm):
    """ 获取配置类型表单校验 """


class PostConfigTypeForm(BaseForm):
    """ 新增配置类型表单校验 """
    name = StringField(validators=[DataRequired('请输入配置类型')])
    desc = StringField()

    def validate_name(self, field):
        if ConfigType.get_first(name=field.data):
            raise ValidationError(f'名为 {field.data} 的配置类型已存在')


class PutConfigTypeForm(PostConfigTypeForm):
    """ 修改配置类型表单校验 """
    id = IntegerField(validators=[DataRequired('配置类型id必传')])

    def validate_id(self, field):
        old_conf_type = ConfigType.get_first(id=field.data)
        if not old_conf_type:
            raise ValidationError(f'id为 {field.data} 的配置类型不存在')
        setattr(self, 'conf_type', old_conf_type)

    def validate_name(self, field):
        old_conf_type = ConfigType.get_first(name=field.data)
        if old_conf_type and old_conf_type.id != self.id.data:
            raise ValidationError(f'名为 {field.data} 的配置类型已存在')
        setattr(self, 'conf_type', old_conf_type)


class GetConfigListForm(BaseForm):
    """ 获取配置列表 """
    type = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class DeleteConfigForm(BaseForm):
    """ 删除配置表单校验 """
    id = IntegerField(validators=[DataRequired('配置id必传')])

    def validate_id(self, field):
        conf = Config.get_first(id=field.data)
        if not conf:
            raise ValidationError(f'id为 {field.data} 的配置不存在')
        setattr(self, 'conf', conf)


class GetConfigForm(DeleteConfigForm):
    """ 获取配置表单校验 """


class PostConfigForm(BaseForm):
    """ 新增配置表单校验 """
    name = StringField(validators=[DataRequired('请输入配置名')])
    value = StringField(validators=[DataRequired('请输入配置的值')])
    type = StringField(validators=[DataRequired('请输入配置的类型')])
    desc = StringField()

    def validate_name(self, field):
        if Config.get_first(name=field.data):
            raise ValidationError(f'名为 {field.data} 的配置已存在')


class PutConfigForm(PostConfigForm):
    """ 修改配置表单校验 """
    id = IntegerField(validators=[DataRequired('配置id必传')])

    def validate_name(self, field):
        conf = Config.get_first(name=field.data)
        if conf.id != self.id.data:
            raise ValidationError(f'名为 {field.data} 的配置已存在')
        setattr(self, 'conf', conf)
