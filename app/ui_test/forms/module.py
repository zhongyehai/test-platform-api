# -*- coding: utf-8 -*-

from wtforms import StringField, IntegerField
from wtforms.validators import Length, DataRequired

from app.baseForm import BaseForm
from app.ui_test.models.page import UiPage
from app.ui_test.models.project import UiProject
from app.ui_test.models.module import UiModule


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
        project = self.validate_data_is_exist(f'id为【{field.data}】的项目不存在', UiProject, id=field.data)
        setattr(self, 'project', project)

    def validate_name(self, field):
        """ 模块名不重复 """
        self.validate_data_is_not_exist(
            f'当前模块下已存在名为【{field.data}】的模块',
            UiModule,
            project_id=self.project_id.data,
            level=self.level.data,
            name=field.data,
            parent=self.parent.data
        )


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
        module = self.validate_data_is_exist(f'id为【{field.data}】的模块不存在', UiModule, id=field.data)
        setattr(self, 'module', module)


class ModuleIdForm(BaseForm):
    """ 返回待编辑模块信息 """
    id = IntegerField(validators=[DataRequired('模块id必传')])

    def validate_id(self, field):
        module = self.validate_data_is_exist(f'id为【{field.data}】的模块不存在', UiModule, id=field.data)
        setattr(self, 'module', module)


class DeleteModelForm(ModuleIdForm):
    """ 删除模块 """

    def validate_id(self, field):
        module = self.validate_data_is_exist(f'id为【{field.data}】的模块不存在', UiModule, id=field.data)
        self.validate_data_is_true('不能删除别人项目下的模块', UiProject.is_can_delete(module.project_id, module))
        self.validate_data_is_not_exist('请先删除模块下的页面', UiPage, module_id=module.id)
        self.validate_data_is_not_exist('请先删除当前模块下的子模块', UiModule, parent=module.id)
        setattr(self, 'module', module)


class EditModelForm(ModuleIdForm, AddModelForm):
    """ 修改模块的校验 """

    def validate_id(self, field):
        """ 模块必须存在 """
        old_module = self.validate_data_is_exist(f'id为【{field.data}】的模块不存在', UiModule, id=field.data)
        setattr(self, 'old_module', old_module)

    def validate_name(self, field):
        """ 同一个项目下，模块名不重复 """
        self.validate_data_is_not_repeat(
            f'id为【{self.project_id.data}】的项目下已存在名为【{field.data}】的模块',
            UiModule,
            self.id.data,
            project_id=self.project_id.data,
            level=self.level.data,
            name=field.data,
            parent=self.parent.data
        )
