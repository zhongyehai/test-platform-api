# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

from app.system.models.business import BusinessLine
from app.baseForm import BaseForm


class GetBusinessListForm(BaseForm):
    """ 获取业务线列表 """
    name = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()
    create_user = StringField()
    code = StringField()


class BusinessIdForm(BaseForm):
    """ 业务线id存在 """
    id = IntegerField(validators=[DataRequired("业务线id必传")])

    def validate_id(self, field):
        business = self.validate_data_is_exist(f"id为 {field.data} 的配置业务线不存在", BusinessLine, id=field.data)
        setattr(self, "business", business)


class DeleteBusinessForm(BusinessIdForm):
    """ 删除业务线表单校验 """


class GetBusinessForm(BusinessIdForm):
    """ 获取业务线表单校验 """


class PostBusinessForm(BaseForm):
    """ 新增业务线表单校验 """
    name = StringField(validators=[DataRequired("请输业务线名字")])
    code = StringField(validators=[DataRequired("请输业务线code")])
    num = StringField()
    desc = StringField()

    def validate_name(self, field):
        self.validate_data_is_not_exist(f"名为 {field.data} 的业务线名字已存在", BusinessLine, name=field.data)

    def validate_code(self, field):
        self.validate_data_is_not_exist(f"业务线code {field.data} 已存在", BusinessLine, code=field.data)


class PutBusinessForm(BusinessIdForm, PostBusinessForm):
    """ 修改业务线表单校验 """

    def validate_name(self, field):
        self.validate_data_is_not_repeat(
            f"名为 {field.data} 的业务线名字已存在",
            BusinessLine,
            self.id.data,
            name=field.data
        )

    def validate_code(self, field):
        self.validate_data_is_not_repeat(
            f"业务线code {field.data} 已存在",
            BusinessLine,
            self.id.data,
            code=field.data
        )
