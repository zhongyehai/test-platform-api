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
from ..element.models import UiElement
from ..page.models import UiPage
from ..module.models import UiModule
from ..project.models import UiProject


class AddPageForm(BaseForm):
    """ 添加页面信息的校验 """
    project_id = StringField(validators=[DataRequired('项目id必传')])
    module_id = StringField(validators=[DataRequired('模块id必传')])

    name = StringField(validators=[DataRequired('页面名必传'), Length(1, 255, '页面名长度为1~255位')])
    desc = StringField()
    addr = StringField()
    num = StringField()

    def validate_project_id(self, field):
        """ 校验项目id """
        project = UiProject.get_first(id=field.data)
        if not project:
            raise ValidationError(f'id为【{field.data}】的项目不存在')
        setattr(self, 'project', project)

    def validate_module_id(self, field):
        """ 校验模块id """
        if not UiModule.get_first(id=field.data):
            raise ValidationError(f'id为【{field.data}】的模块不存在')

    def validate_name(self, field):
        """ 校验同一模块下页面名不重复 """
        if UiPage.get_first(name=field.data, module_id=self.module_id.data):
            raise ValidationError(f'当前模块下，名为【{field.data}】的页面已存在')


class EditPageForm(AddPageForm):
    """ 修改页面信息 """
    id = IntegerField(validators=[DataRequired('页面id必传')])

    def validate_id(self, field):
        """ 校验页面id已存在 """
        old = UiPage.get_first(id=field.data)
        if not old:
            raise ValidationError(f'id为【{field.data}】的页面不存在')
        setattr(self, 'old', old)

    def validate_name(self, field):
        """ 校验页面名不重复 """
        old_api = UiPage.get_first(name=field.data, module_id=self.module_id.data)
        if old_api and old_api.id != self.id.data:
            raise ValidationError(f'当前模块下，名为【{field.data}】的页面已存在')


class ValidateProjectId(BaseForm):
    """ 校验项目id """
    projectId = IntegerField(validators=[DataRequired('项目id必传')])

    def validate_projectId(self, field):
        """ 校验项目id """
        if not UiProject.get_first(id=field.data):
            raise ValidationError(f'id为【{field.data}】的项目不存在')


class PageListForm(BaseForm):
    """ 查询页面信息 """
    moduleId = IntegerField(validators=[DataRequired('请选择模块')])
    name = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class GetPageById(BaseForm):
    """ 待编辑信息 """
    id = IntegerField(validators=[DataRequired('页面id必传')])

    def validate_id(self, field):
        api = UiPage.get_first(id=field.data)
        if not api:
            raise ValidationError(f'id为【{field.data}】的页面不存在')
        setattr(self, 'api', api)


class DeletePageForm(GetPageById):
    """ 删除页面 """

    def validate_id(self, field):
        api = UiPage.get_first(id=field.data)
        # 页面不存在
        if not api:
            raise ValidationError(f'id为【{field.data}】的页面不存在')

        # 页面下有元素
        if UiElement.get_first(page_id=field.data):
            raise ValidationError(f'当前页面下有元素，请先删除元素，再删除页面')

        # 校验页面是否被测试用例引用
        # case_data = Step.get_first(api_id=field.data)
        # if case_data:
        #     case = Case.get_first(id=case_data.case_id)
        #     raise ValidationError(f'用例【{case.name}】已引用此页面，请先解除引用')

        project_id = UiModule.get_first(id=api.module_id).project_id
        if not UiProject.is_can_delete(project_id, api):
            raise ValidationError('不能删除别人项目下的页面')
        setattr(self, 'api', api)
