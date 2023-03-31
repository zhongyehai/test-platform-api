# -*- coding: utf-8 -*-
import validators
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, ValidationError

from app.config.models.runEnv import RunEnv
from app.baseForm import BaseForm


class GetRunEnvListForm(BaseForm):
    """ 获取环境列表 """
    pageNum = IntegerField()
    pageSize = IntegerField()
    create_user = StringField()
    name = StringField()
    group = StringField()
    code = StringField()


class RunEnvIdForm(BaseForm):
    """ 环境id存在 """
    id = IntegerField(validators=[DataRequired("环境id必传")])

    def validate_id(self, field):
        run_env = self.validate_data_is_exist(f"id为 {field.data} 的环境不存在", RunEnv, id=field.data)
        setattr(self, "run_env", run_env)


class DeleteRunEnvForm(RunEnvIdForm):
    """ 删除环境表单校验 """


class GetRunEnvForm(RunEnvIdForm):
    """ 获取环境表单校验 """


class PostRunEnvForm(BaseForm):
    """ 新增环境表单校验 """
    name = StringField(validators=[DataRequired("请输入环境名字")])
    code = StringField(validators=[DataRequired("请输入code")])
    group = StringField(validators=[DataRequired("请选则环境分组")])
    desc = StringField()
    num = StringField()

    def validate_code(self, field):
        """ code不允许重复 """
        self.validate_data_is_not_exist(
            f"code【{field.data}】已存在",
            RunEnv,
            code=field.data
        )


class PutRunEnvForm(RunEnvIdForm, PostRunEnvForm):
    """ 修改环境表单校验 """

    def validate_code(self, field):
        """ code不允许重复 """
        self.validate_data_is_not_repeat(
            f"code【{field.data}】已存在",
            RunEnv,
            self.id.data,
            code=field.data
        )
