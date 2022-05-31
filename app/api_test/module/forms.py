# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, Length, DataRequired

from app.baseForm import BaseForm
from ..project.models import ApiProject
from .models import ApiModule


class AddModelForm(BaseForm):
    """ 添加模块的校验 """
    project_id = IntegerField(validators=[DataRequired('服务id必传')])
    name = StringField(validators=[DataRequired('模块名必传'), Length(1, 255, message='模块名称为1~255位')])
    level = StringField()
    parent = StringField()
    id = StringField()
    num = StringField()

    def validate_project_id(self, field):
        """ 服务id合法 """
        project = ApiProject.get_first(id=field.data)
        if not project:
            raise ValidationError(f'id为【{field.data}】的服务不存在，请先创建')
        setattr(self, 'project', project)

    def validate_name(self, field):
        """ 模块名不重复 """
        old_module = ApiModule.get_first(
            project_id=self.project_id.data, level=self.level.data, name=field.data, parent=self.parent.data
        )
        if old_module:
            raise ValidationError(f'当前服务中已存在名为【{field.data}】的模块')


class FindModelForm(BaseForm):
    """ 查找模块 """
    projectId = IntegerField(validators=[DataRequired('服务id必传')])
    name = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class GetModelForm(BaseForm):
    """ 获取模块信息 """
    id = IntegerField(validators=[DataRequired('模块id必传')])

    def validate_id(self, field):
        module = ApiModule.get_first(id=field.data)
        if not module:
            raise ValidationError(f'id为【{field.data}】的模块不存在')
        setattr(self, 'module', module)


class ModuleIdForm(BaseForm):
    """ 返回待编辑模块信息 """
    id = IntegerField(validators=[DataRequired('模块id必传')])

    def validate_id(self, field):
        module = ApiModule.get_first(id=field.data)
        if not module:
            raise ValidationError(f'id为【{field.data}】的模块不存在')
        setattr(self, 'module', module)


class DeleteModelForm(ModuleIdForm):
    """ 删除模块 """

    def validate_id(self, field):
        module = ApiModule.get_first(id=field.data)
        if not module:
            raise ValidationError(f'id为【{field.data}】的模块不存在')
        if not ApiProject.is_can_delete(module.project_id, module):
            raise ValidationError('不能删除别人服务下的模块')
        if module.apis:
            raise ValidationError('请先删除模块下的接口')
        if ApiModule.get_first(parent=module.id):
            raise ValidationError('请先删除当前模块下的子模块')

        setattr(self, 'module', module)


class EditModelForm(ModuleIdForm, AddModelForm):
    """ 修改模块的校验 """

    def validate_id(self, field):
        """ 模块必须存在 """
        old_module = ApiModule.get_first(id=field.data)
        if not old_module:
            raise ValidationError(f'id为【{field.data}】的模块不存在')
        setattr(self, 'old_module', old_module)

    def validate_name(self, field):
        """ 同一个服务下，模块名不重复 """
        old_module = ApiModule.get_first(
            project_id=self.project_id.data, level=self.level.data, name=field.data, parent=self.parent.data
        )
        if old_module and old_module.id != self.id.data:
            raise ValidationError(f'id为【{self.project_id.data}】的服务下已存在名为【{field.data}】的模块')


class StickModuleForm(BaseForm):
    """ 置顶模块 """
    project_id = IntegerField(validators=[DataRequired('服务id必传')])
    id = IntegerField(validators=[DataRequired('模块id必传')])
