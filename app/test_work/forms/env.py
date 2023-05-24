# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

from app.baseForm import BaseForm
from ..models.env import Env


class GetEnvListForm(BaseForm):
    """ 获取数据列表 """
    page_num = IntegerField()
    page_size = IntegerField()
    business = IntegerField()
    name = StringField()
    parent = StringField()
    source_type = StringField()
    value = StringField()


class GetEnvForm(BaseForm):
    """ 数据详情 """
    id = IntegerField(validators=[DataRequired("数据id必传")])

    def validate_id(self, field):
        env = self.validate_data_is_exist(f"id为 {field.data} 的数据不存在", Env, id=field.data)
        setattr(self, "env", env)


class DeleteEnvForm(GetEnvForm):
    """ 删除数据 """


class AddEnvForm(BaseForm):
    """ 添加数据 """
    business = IntegerField()
    source_type = StringField(validators=[DataRequired("请选择资源类型")])
    data_list = StringField(validators=[DataRequired("数据必传")])
    num = StringField()
    parent = StringField()

    def validate_source_type(self, field):
        """ 校验必填项 """
        if field.data == "addr":  # 新增地址，则业务线必传
            self.validate_data_is_true('业务线必传', self.business.data)
        else:  # 新增账号，则父级id必传
            self.validate_data_is_true('父级资源必传', self.parent.data)

    def validate_data_list(self, field):
        """ 校验数据项
        [{"name": "", "value": "", "password": "", "desc": ""}]
        """
        for index, data in enumerate(field.data):
            if not data.get("name") or not data.get("value"):
                raise ValueError(f'第【{index + 1}】行，名字和值必填')


class ChangeEnvForm(GetEnvForm):
    """ 修改数据 """

    business = IntegerField()
    name = StringField(validators=[DataRequired("请输入资源名字")])
    source_type = StringField(validators=[DataRequired("请选择资源类型")])
    value = StringField(validators=[DataRequired("请输入资源对应的值")])
    password = StringField()
    num = StringField()
    parent = StringField()
    desc = StringField()
