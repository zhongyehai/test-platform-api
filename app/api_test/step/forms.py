# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Length

from ..apiMsg.models import ApiMsg
from ..case.models import ApiCase
from app.baseForm import BaseForm
from ..func.models import Func
from ..project.models import ApiProject, ApiProjectEnv
from .models import ApiStep


class GetStepListForm(BaseForm):
    """ 根据用例id获取步骤列表 """
    caseId = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_caseId(self, field):
        case = ApiCase.get_first(id=field.data)
        if not case:
            raise ValidationError(f'id为 {field.data} 的用例不存在')
        setattr(self, 'case', case)


class GetStepForm(BaseForm):
    """ 根据步骤id获取步骤 """
    id = IntegerField(validators=[DataRequired('步骤id必传')])

    def validate_id(self, field):
        step = ApiStep.get_first(id=field.data)
        if not step:
            raise ValidationError(f'id为 {field.data} 的步骤不存在')
        setattr(self, 'step', step)


class AddStepForm(BaseForm):
    """ 添加步骤校验 """
    project_id = IntegerField()
    case_id = IntegerField(validators=[DataRequired('用例id必传')])
    api_id = IntegerField()
    quote_case = IntegerField()

    name = StringField(validators=[DataRequired('步骤名称不能为空'), Length(1, 255, message='步骤名长度为1~255位')])
    up_func = StringField()
    down_func = StringField()
    is_run = IntegerField()
    run_times = IntegerField()
    headers = StringField()
    params = StringField()
    data_form = StringField()
    data_json = StringField()
    data_xml = StringField()
    extracts = StringField()
    validates = StringField()
    data_driver = StringField()
    num = StringField()

    def validate_project_id(self, field):
        """ 校验服务id """
        if not self.quote_case.data:
            project = ApiProject.get_first(id=field.data)
            if not project:
                raise ValidationError(f'id为【{field.data}】的服务不存在')
            setattr(self, 'project', project)

    def validate_case_id(self, field):
        """ 校验用例存在 """
        case = ApiCase.get_first(id=field.data)
        if not case:
            raise ValidationError(f'id为【{field.data}】的用例不存在')
        setattr(self, 'case', case)

    def validate_api_id(self, field):
        """ 校验接口存在 """
        if not self.quote_case.data:
            if not ApiMsg.get_first(id=field.data):
                raise ValidationError(f'id为【{field.data}】的接口不存在')

    def validate_quote_case(self, field):
        """ 不能自己引用自己 """
        if field.data and field.data == self.case_id:
            raise ValidationError(f'不能自己引用自己')

    def validate_extracts(self, field):
        """ 校验数据提取信息 """
        if not self.quote_case.data:
            self.validate_base_extracts(field.data)

    def validate_validates(self, field):
        """ 校验断言信息 """
        if not self.quote_case.data:
            func_files = self.loads(
                ApiProjectEnv.get_first(project_id=self.project.id, env=self.case.choice_host).func_files)
            func_container = Func.get_func_by_func_file_name(func_files)
            self.validate_base_validates(field.data, func_container)


class EditStepForm(AddStepForm):
    """ 修改步骤校验 """
    id = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_id(self, field):
        """ 校验步骤id已存在 """
        step = ApiStep.get_first(id=field.data)
        if not step:
            raise ValidationError(f'id为【{field.data}】的步骤不存在')
        setattr(self, 'step', step)
