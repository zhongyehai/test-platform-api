# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, Length

from app.assist.models.dataPool import DataPool
from app.baseForm import BaseForm


class HasDataPoolForm(BaseForm):
    """ 校验数据池数据存在 """
    id = StringField()

    def validate_id(self, field):
        if field.data:
            data_pool = self.validate_data_is_exist(f'id为 【{field.data}】 的数据不存在', DataPool, id=field.data)
            setattr(self, "data_pool", data_pool)


class GetDataPoolForm(BaseForm):
    """ 获取数据池列表/新增数据池数据 """
    pageNum = IntegerField()
    pageSize = IntegerField()
    env = StringField()
    mobile = StringField()
    business_order_no = StringField()
    business_status = StringField()
    use_status = StringField()


class PostDataPoolForm(GetDataPoolForm):
    """ 新增数据池数据 """
    env = StringField(validators=[DataRequired("请选择环境")])
    desc = StringField(validators=[Length(0, 255, "描述文字超长，请控制在255位以内")])
    mobile = StringField(validators=[Length(0, 32, "手机号超长，请控制在32位以内")])
    password = StringField(validators=[Length(0, 32, "密码超长，请控制在32位以内")])
    business_order_no = StringField(validators=[DataRequired("流水号必填"), Length(1, 64, "流水号超长，请控制在64位以内")])


class PutDataPoolForm(HasDataPoolForm, PostDataPoolForm):
    """ 修改数据池数据 """


class DeleteDataPoolForm(HasDataPoolForm):
    """ 删除数据池数据 """
