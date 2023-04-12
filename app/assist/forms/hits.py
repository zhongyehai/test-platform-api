# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

from app.baseForm import BaseForm
from app.assist.models.hits import Hits


class GetHitListForm(BaseForm):
    """ 获取自动化测试命中问题列表 """
    date = StringField()
    hit_type = StringField()
    test_type = StringField()
    hit_detail = StringField()
    report_id = IntegerField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class HasHitForm(BaseForm):
    """ 获取自定义自动化测试命中问题 """
    id = IntegerField(validators=[DataRequired("请输选择自动化测试命中问题")])

    def validate_id(self, field):
        """ 校验自定义自动化测试命中问题需存在 """
        hit = self.validate_data_is_exist(f'id为 【{field.data}】 的命中不存在', Hits, id=field.data)
        setattr(self, "hit", hit)


class CreatHitForm(BaseForm):
    """ 创建自定义自动化测试命中问题 """
    date = StringField(validators=[DataRequired("问题触发日期必传")])
    hit_type = StringField(validators=[DataRequired("请选择问题类型")])
    test_type = StringField(validators=[DataRequired("请输入测试类型")])
    hit_detail = StringField(validators=[DataRequired("请输入问题内容")])
    project_id = IntegerField(validators=[DataRequired("请输入服务id")])
    env = StringField(validators=[DataRequired("请选则环境")])
    report_id = IntegerField(validators=[DataRequired("请输入测试报告id")])
    desc = StringField()

    def validate_date(self, filed):
        self.date.data = filed.data[0:10]


class EditHitForm(HasHitForm, CreatHitForm):
    """ 修改自定义自动化测试命中问题 """
