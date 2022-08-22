# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, Length

from app.api_test.models.api import ApiMsg
from app.api_test.models.case import ApiCase
from app.baseForm import BaseForm
from app.assist.models.func import Func
from app.api_test.models.project import ApiProject, ApiProjectEnv
from app.api_test.models.step import ApiStep


class GetStepListForm(BaseForm):
    """ 根据用例id获取步骤列表 """
    caseId = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_caseId(self, field):
        case = self.validate_data_is_exist(f'id为 {field.data} 的用例不存在', ApiCase, id=field.data)
        setattr(self, 'case', case)


class GetStepForm(BaseForm):
    """ 根据步骤id获取步骤 """
    id = IntegerField(validators=[DataRequired('步骤id必传')])

    def validate_id(self, field):
        step = self.validate_data_is_exist(f'id为 {field.data} 的步骤不存在', ApiStep, id=field.data)
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
    data_type = StringField()
    data_form = StringField()
    data_json = StringField()
    data_text = StringField()
    extracts = StringField()
    validates = StringField()
    data_driver = StringField()
    num = StringField()
    time_out = IntegerField()

    def validate_project_id(self, field):
        """ 校验服务id """
        if not self.quote_case.data:
            project = self.validate_data_is_exist(f'id为【{field.data}】的服务不存在', ApiProject, id=field.data)
            setattr(self, 'project', project)

    def validate_case_id(self, field):
        """ 校验用例存在 """
        case = self.validate_data_is_exist(f'id为 {field.data} 的用例不存在', ApiCase, id=field.data)
        setattr(self, 'case', case)

    def validate_api_id(self, field):
        """ 校验接口存在 """
        if not self.quote_case.data:
            api = self.validate_data_is_exist(f'id为【{field.data}】的接口不存在', ApiMsg, id=field.data)
            setattr(self, 'api', api)

    def validate_quote_case(self, field):
        """ 不能自己引用自己 """
        if field.data:
            self.validate_data_is_true(f'不能自己引用自己', field.data != self.case_id.data)

    def validate_extracts(self, field):
        """ 校验数据提取信息 """
        if not self.quote_case.data:
            self.validate_base_extracts(field.data)

    def validate_validates(self, field):
        """ 校验断言信息 """
        if not self.quote_case.data:
            func_container = Func.get_func_by_func_file_name(self.loads(self.project.func_files))
            self.validate_base_validates(field.data, func_container)


class EditStepForm(AddStepForm):
    """ 修改步骤校验 """
    id = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_id(self, field):
        """ 校验步骤id已存在 """
        step = self.validate_data_is_exist(f'id为 {field.data} 的步骤不存在', ApiStep, id=field.data)
        setattr(self, 'step', step)
