# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Length

from app.app_ui_test.models.element import AppUiElement as Element
from app.app_ui_test.models.case import AppUiCase as Case
from app.app_ui_test.models.step import AppUiStep as Step
from app.baseForm import BaseForm


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
    case_id = IntegerField(validators=[DataRequired("用例id必传")])
    element_id = IntegerField()
    quote_case = IntegerField()
    name = StringField(validators=[DataRequired("步骤名称不能为空"), Length(1, 255, message="步骤名长度为1~255位")])
    execute_type = StringField()
    send_keys = StringField()
    up_func = StringField(default=[])
    down_func = StringField(default=[])
    status = IntegerField()
    run_times = IntegerField()
    extracts = StringField()
    skip_on_fail = StringField()
    skip_if = StringField()
    validates = StringField()
    data_driver = StringField()
    num = StringField()
    wait_time_out = IntegerField()

    def validate_extracts(self, field):
        """ 校验数据提取 """
        if not self.quote_case.data:
            self.validate_ui_extracts(field.data)

    def validate_element_id(self, field):
        """ 校验元素存在 """
        if not self.quote_case.data:
            self.validate_data_is_exist(f"id为 {field.data} 的元素不存在", Element, id=field.data)

    def validate_case_id(self, field):
        """ 校验用例存在 """
        case = self.validate_data_is_exist(f"id为 {field.data} 的用例不存在", Case, id=field.data)
        setattr(self, "case", case)

    def validate_quote_case(self, field):
        """ 不能自己引用自己 """
        self.validate_data_is_false("不能自己引用自己", field.data and field.data == self.case_id)

    def validate_execute_type(self, field):
        """ 如果不是引用用例，则执行方式不能为空 """
        if not self.quote_case.data:
            if not field.data:
                raise ValidationError("执行方式不能为空")
            if "dict" in field.data:  # 校验输入字典的项能不能序列化和反序列化
                try:
                    self.loads(self.send_keys.data)
                except Exception as error:
                    raise ValidationError(f"【{self.send_keys.data}】不能转为json，请确认")

    def validate_validates(self, field):
        """ 校验断言信息 """
        if not self.quote_case.data:
            self.validate_base_validates(field.data)


class EditStepForm(AddStepForm):
    """ 修改步骤校验 """
    id = IntegerField(validators=[DataRequired("用例id必传")])

    def validate_id(self, field):
        """ 校验步骤id已存在 """
        step = self.validate_data_is_exist(f"id为【{field.data}】的步骤不存在", Step, id=field.data)
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
