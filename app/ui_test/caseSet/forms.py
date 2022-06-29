# -*- coding: utf-8 -*-

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
        set = self.validate_data_is_exist(f'id为【{field.data}】的用例集不存在', UiCaeSet, id=field.data)
        setattr(self, 'set', set)


class RunCaseSetForm(GetCaseSetForm):
    """ 运行用例集 """
    is_async = IntegerField()
    env = StringField()

    def validate_id(self, field):
        set = self.validate_data_is_exist(f'id为【{field.data}】的用例集不存在', UiCaeSet, id=field.data)
        self.validate_data_is_exist(f'用例集下没有用例', UiCase, set_id=field.data)
        setattr(self, 'set', set)


class AddCaseSetForm(BaseForm):
    """ 添加用例集的校验 """
    project_id = StringField(validators=[DataRequired('请先选择首页项目')])
    name = StringField(validators=[DataRequired('用例集名称不能为空'), Length(1, 255, message='用例集名长度为1~255位')])
    level = StringField()
    parent = StringField()
    id = StringField()
    num = StringField()

    def validate_project_id(self, field):
        """ 项目id存在 """
        project = self.validate_data_is_exist(f'id为【{field.data}】的项目不存在，请先创建', UiProject, id=field.data)
        setattr(self, 'project', project)

    def validate_name(self, field):
        """ 校验用例集名不重复 """
        self.validate_data_is_not_exist(
            f'用例集名字【{field.data}】已存在',
            UiCaeSet,
            project_id=self.project_id.data,
            level=self.level.data,
            name=field.data,
            parent=self.parent.data
        )


class GetCaseSetEditForm(BaseForm):
    """ 返回待编辑用例集合 """
    id = IntegerField(validators=[DataRequired('用例集id必传')])

    def validate_id(self, field):
        set = self.validate_data_is_exist('没有此用例集', UiCaeSet, id=field.data)
        setattr(self, 'set', set)


class DeleteCaseSetForm(GetCaseSetEditForm):
    """ 删除用例集 """

    def validate_id(self, field):
        case_set = UiCaeSet.get_first(id=field.data)
        # 数据权限
        self.validate_data_is_true('不能删除别人项目下的用例集', UiProject.is_can_delete(case_set.project_id, case_set))

        # 用例集下是否有用例集
        self.validate_data_is_false('请先删除当前用例集下的用例集', UiCaeSet.get_first(parent=field.data))

        # 用例集下是否有用例
        self.validate_data_is_false('请先删除当前用例集下的用例', UiCase.get_first(set_id=field.data))

        setattr(self, 'case_set', case_set)


class EditCaseSetForm(GetCaseSetEditForm, AddCaseSetForm):
    """ 编辑用例集 """

    def validate_id(self, field):
        """ 用例集id已存在 """
        case_set = self.validate_data_is_exist(f'不存在id为【{field.data}】的用例集', UiCaeSet, id=field.data)
        setattr(self, 'case_set', case_set)

    def validate_name(self, field):
        """ 校验用例集名不重复 """
        self.validate_data_is_not_repeat(
            f'用例集名字【{field.data}】已存在',
            UiCaeSet,
            self.id.data,
            project_id=self.project_id.data,
            level=self.level.data,
            name=field.data,
            parent=self.parent.data
        )


class FindCaseSet(BaseForm):
    """ 查找用例集合 """
    pageNum = IntegerField()
    pageSize = IntegerField()
    name = StringField()
    projectId = IntegerField(validators=[DataRequired('项目id必传')])

    def validate_projectId(self, field):
        project = self.validate_data_is_exist(f'id为【{field.data}】的项目不存在', UiProject, id=field.data)
        setattr(self, 'all_sets', project.case_sets)
