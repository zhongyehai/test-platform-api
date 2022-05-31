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
from ..page.models import UiPage
from ..project.models import UiProject
from .models import UiModule


class AddModelForm(BaseForm):
    """ 添加模块的校验 """
    project_id = IntegerField(validators=[DataRequired('项目id必传')])
    name = StringField(validators=[DataRequired('模块名必传'), Length(1, 255, message='模块名称为1~255位')])
    level = StringField()
    parent = StringField()
    id = StringField()
    num = StringField()

    def validate_project_id(self, field):
        """ 项目id合法 """
        project = UiProject.get_first(id=field.data)
        if not project:
            raise ValidationError(f'id为【{field.data}】的项目不存在，请先创建')
        setattr(self, 'project', project)

    def validate_name(self, field):
        """ 模块名不重复 """
        old_module = UiModule.get_first(
            project_id=self.project_id.data, level=self.level.data, name=field.data, parent=self.parent.data
        )
        if old_module:
            raise ValidationError(f'当前项目中已存在名为【{field.data}】的模块')


class FindModelForm(BaseForm):
    """ 查找模块 """
    projectId = IntegerField(validators=[DataRequired('项目id必传')])
    name = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class GetModelForm(BaseForm):
    """ 获取模块信息 """
    id = IntegerField(validators=[DataRequired('模块id必传')])

    def validate_id(self, field):
        module = UiModule.get_first(id=field.data)
        if not module:
            raise ValidationError(f'id为【{field.data}的模块不存在')
        setattr(self, 'module', module)


class ModuleIdForm(BaseForm):
    """ 返回待编辑模块信息 """
    id = IntegerField(validators=[DataRequired('模块id必传')])

    def validate_id(self, field):
        module = UiModule.get_first(id=field.data)
        if not module:
            raise ValidationError(f'id为【{field.data}】的模块不存在')
        setattr(self, 'module', module)


class DeleteModelForm(ModuleIdForm):
    """ 删除模块 """

    def validate_id(self, field):
        module = UiModule.get_first(id=field.data)
        if not module:
            raise ValidationError(f'id为【{field.data}】的模块不存在')
        if not UiProject.is_can_delete(module.project_id, module):
            raise ValidationError('不能删除别人项目下的模块')
        if UiPage.get_first(module_id=module.id):
            raise ValidationError('请先删除模块下的页面')
        if UiModule.get_first(parent=module.id):
            raise ValidationError('请先删除当前模块下的子模块')

        setattr(self, 'module', module)


class EditModelForm(ModuleIdForm, AddModelForm):
    """ 修改模块的校验 """

    def validate_id(self, field):
        """ 模块必须存在 """
        old_module = UiModule.get_first(id=field.data)
        if not old_module:
            raise ValidationError(f'id为【{field.data}】的模块不存在')
        setattr(self, 'old_module', old_module)

    def validate_name(self, field):
        """ 同一个项目下，模块名不重复 """
        old_module = UiModule.get_first(
            project_id=self.project_id.data, level=self.level.data, name=field.data, parent=self.parent.data
        )
        if old_module and old_module.id != self.id.data:
            raise ValidationError(f'id为【{self.project_id.data}】的项目下已存在名为【{field.data}】的模块')


class StickModuleForm(BaseForm):
    """ 置顶模块 """
    project_id = IntegerField(validators=[DataRequired('项目id必传')])
    id = IntegerField(validators=[DataRequired('模块id必传')])
