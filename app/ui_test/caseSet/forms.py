# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:10
# @Author : ZhongYeHai
# @Site :
# @File : forms.py
# @Software: PyCharm
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, Length, DataRequired

from app.baseForm import BaseForm
from ..case.models import UiCase
from ..project.models import UiProject
from .models import UiCaeSet


class GetCaseSetForm(BaseForm):
    """ 获取用例集信息 """
    id = IntegerField(validators=[DataRequired('用例集id必传')])

    def validate_id(self, field):
        set = UiCaeSet.get_first(id=field.data)
        if not set:
            raise ValidationError(f'id为【{field.data}】的模块不存在')
        setattr(self, 'set', set)


class AddCaseSetForm(BaseForm):
    """ 添加用例集的校验 """
    project_id = StringField(validators=[DataRequired('请先选择首页服务')])
    name = StringField(validators=[DataRequired('用例集名称不能为空'), Length(1, 255, message='用例集名长度为1~255位')])
    level = StringField()
    parent = StringField()
    id = StringField()
    num = StringField()

    def validate_project_id(self, field):
        """ 服务id合法 """
        project = UiProject.get_first(id=field.data)
        if not project:
            raise ValidationError(f'id为【{field.data}】的服务不存在，请先创建')
        setattr(self, 'project', project)

    def validate_name(self, field):
        """ 校验用例集名不重复 """
        if UiCaeSet.get_first(project_id=self.project_id.data,
                         level=self.level.data,
                         name=field.data,
                         parent=self.parent.data):
            raise ValidationError(f'用例集名字【{field.data}】已存在')


class GetCaseSetEditForm(BaseForm):
    """ 返回待编辑用例集合 """
    id = IntegerField(validators=[DataRequired('用例集id必传')])

    def validate_id(self, field):
        set = UiCaeSet.get_first(id=field.data)
        if not set:
            raise ValidationError('没有此用例集')
        setattr(self, 'set', set)


class DeleteCaseSetForm(GetCaseSetEditForm):
    """ 删除用例集 """

    def validate_id(self, field):
        case_set = UiCaeSet.get_first(id=field.data)
        # 数据权限
        if not UiProject.is_can_delete(case_set.project_id, case_set):
            raise ValidationError('不能删除别人服务下的用例集')
        # 用例集下是否有用例集
        if UiCaeSet.get_first(parent=field.data):
            raise ValidationError('请先删除当前用例集下的用例集')
        # 用例集下是否有用例
        if UiCase.get_first(set_id=field.data):
            raise ValidationError('请先删除当前用例集下的用例')
        setattr(self, 'case_set', case_set)


class EditCaseSetForm(GetCaseSetEditForm, AddCaseSetForm):
    """ 编辑用例集 """

    def validate_id(self, field):
        """ 用例集id已存在 """
        case_set = UiCaeSet.get_first(id=field.data)
        if not case_set:
            raise ValidationError(f'不存在id为【{field.data}】的用例集')
        setattr(self, 'case_set', case_set)

    def validate_name(self, field):
        """ 校验用例集名不重复 """
        old_set = UiCaeSet.get_first(project_id=self.project_id.data, level=self.level.data, name=field.data, parent=self.parent.data)
        if old_set and old_set.id != self.id.data:
            raise ValidationError(f'用例集名字【{field.data}】已存在')


class FindCaseSet(BaseForm):
    """ 查找用例集合 """
    pageNum = IntegerField()
    pageSize = IntegerField()
    name = StringField()
    projectId = IntegerField(validators=[DataRequired('服务id必传')])

    def validate_projectId(self, field):
        project = UiProject.get_first(id=field.data)
        if not project:
            raise ValidationError(f'id为【{field.data}】的服务不存在')
        setattr(self, 'all_sets', project.sets)
