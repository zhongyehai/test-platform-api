# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, Length

from app.baseForm import BaseForm
from app.api_test.models.api import ApiMsg as Api
from app.api_test.models.case import ApiCase as Case
from app.api_test.models.step import ApiStep as Step


class GetStepListForm(BaseForm):
    """ 根据用例id获取步骤列表 """
    caseId = IntegerField(validators=[DataRequired("用例id必传")])

    def validate_caseId(self, field):
        case = self.validate_data_is_exist(f"id为 {field.data} 的用例不存在", Case, id=field.data)
        setattr(self, "case", case)


class GetStepForm(BaseForm):
    """ 根据步骤id获取步骤 """
    id = IntegerField(validators=[DataRequired("步骤id必传")])

    def validate_id(self, field):
        step = self.validate_data_is_exist(f"id为 {field.data} 的步骤不存在", Step, id=field.data)
        setattr(self, "step", step)


class AddStepForm(BaseForm):
    """ 添加步骤校验 """
    name_length = Step.name.property.columns[0].type.length
    api_id = IntegerField()
    case_id = IntegerField(validators=[DataRequired("用例id必传")])
    quote_case = IntegerField()
    name = StringField(validators=[
        DataRequired("步骤名称不能为空"),
        Length(1, name_length, f"步骤长度不可超过{name_length}位")
    ])
    up_func = StringField(default=[])
    down_func = StringField(default=[])
    skip_if = StringField()
    status = IntegerField()
    run_times = IntegerField()
    headers = StringField()
    params = StringField()
    data_type = StringField()
    data_form = StringField()
    data_json = StringField()
    data_urlencoded = StringField()
    data_text = StringField()
    extracts = StringField()
    replace_host = IntegerField()
    skip_on_fail = IntegerField()
    pop_header_filed = StringField()
    validates = StringField()
    data_driver = StringField()
    num = StringField()
    time_out = IntegerField()

    def validate_api_id(self, field):
        """ 校验接口存在 """
        if not self.quote_case.data:
            api = self.validate_data_is_exist(f"id为【{field.data}】的接口不存在", Api, id=field.data)
            setattr(self, "api", api)

    def validate_case_id(self, field):
        """ 校验用例存在 """
        case = self.validate_data_is_exist(f"id为 {field.data} 的用例不存在", Case, id=field.data)
        setattr(self, "case", case)

    def validate_quote_case(self, field):
        """ 不能自己引用自己 """
        if field.data:
            self.validate_data_is_true(f"不能自己引用自己", field.data != self.case_id.data)

    def validate_extracts(self, field):
        """ 校验数据提取信息 """
        if not self.quote_case.data:
            self.validate_api_extracts(field.data)

    def validate_validates(self, field):
        """ 校验断言信息 """
        if not self.quote_case.data:
            self.validate_base_validates(field.data)

    def validate_data_form(self, field):
        self.validate_variable_format(field.data, msg_title='form-data')


class EditStepForm(AddStepForm):
    """ 修改步骤校验 """
    id = IntegerField(validators=[DataRequired("用例id必传")])

    def validate_id(self, field):
        """ 校验步骤id已存在 """
        step = self.validate_data_is_exist(f"id为 {field.data} 的步骤不存在", Step, id=field.data)
        setattr(self, "step", step)


class ChangeStepStatusForm(BaseForm):
    """ 批量修改步骤状态 """
    id = StringField(validators=[DataRequired("步骤id必传")])
    status = IntegerField()

    def validate_id(self, field):
        step_list = []
        for step_id in field.data:
            step = Step.get_first(id=step_id)
            if step:
                step_list.append(step)
        setattr(self, "step_list", step_list)


class DeleteStepForm(BaseForm):
    """ 批量删除步骤 """
    id = StringField(validators=[DataRequired("步骤id必传")])

    def validate_id(self, field):
        step_list = [
            self.validate_data_is_exist(f"id为 {field.data} 的步骤不存在", Step, id=step_id) for step_id in field.data
        ]
        setattr(self, "step_list", step_list)
