# -*- coding: utf-8 -*-

from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Length

from ..element.models import UiElement
from ..case.models import UiCase
from app.baseForm import BaseForm
from ..project.models import UiProject, UiProjectEnv
from .models import UiStep
from ...api_test.func.models import Func


class GetStepListForm(BaseForm):
    """ 根据用例id获取步骤列表 """
    caseId = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_caseId(self, field):
        case = self.validate_data_is_exist(f'id为 {field.data} 的用例不存在', UiCase, id=field.data)
        setattr(self, 'case', case)


class GetStepForm(BaseForm):
    """ 根据步骤id获取步骤 """
    id = IntegerField(validators=[DataRequired('步骤id必传')])

    def validate_id(self, field):
        step = self.validate_data_is_exist(f'id为 {field.data} 的步骤不存在', UiStep, id=field.data)
        setattr(self, 'step', step)


class AddStepForm(BaseForm):
    """ 添加步骤校验 """
    func_file_container = []
    func_container = {}
    project_id = IntegerField()
    page_id = IntegerField()
    case_id = IntegerField(validators=[DataRequired('用例id必传')])
    element_id = IntegerField()
    quote_case = IntegerField()

    name = StringField(validators=[DataRequired('步骤名称不能为空'), Length(1, 255, message='步骤名长度为1~255位')])
    execute_type = StringField()
    send_keys = StringField()
    up_func = StringField()
    down_func = StringField()
    is_run = IntegerField()
    run_times = IntegerField()
    extracts = StringField()
    validates = StringField()
    data_driver = StringField()
    num = StringField()

    def validate_project_id(self, field):
        """ 校验服务id """
        if not self.quote_case.data:
            project = self.validate_data_is_exist(f'id为 {field.data} 的项目不存在', UiProject, id=field.data)
            setattr(self, 'project', project)

    def validate_case_id(self, field):
        """ 校验用例存在 """
        case = self.validate_data_is_exist(f'id为 {field.data} 的用例不存在', UiCase, id=field.data)
        setattr(self, 'case', case)

    def validate_element_id(self, field):
        """ 校验元素存在 """
        if not self.quote_case.data:
            self.validate_data_is_exist(f'id为 {field.data} 的元素不存在', UiElement, id=field.data)

    def validate_quote_case(self, field):
        """ 不能自己引用自己 """
        self.validate_data_is_false('不能自己引用自己', field.data and field.data == self.case_id)

    def validate_execute_type(self, field):
        """ 如果不是引用用例，则执行方式不能为空 """
        if not self.quote_case.data and not field.data:
            raise ValidationError('执行方式不能为空')

    def validate_extracts(self, field):
        """ 校验数据提取信息 """
        # 获取项目配置的函数
        if not self.quote_case.data:
            env = UiProjectEnv.get_first(project_id=self.project.id)
            self.func_file_container = self.loads(env.func_files)

        # 获取用例配置的函数
        self.func_file_container.extend(self.loads(self.case.func_files))
        self.func_container = Func.get_func_by_func_file_name(self.func_file_container)

        # 校验值
        if not self.quote_case.data:
            for index, validate in enumerate(field.data):
                row = f'数据提取，第【{index + 1}】行，'
                extract_type, key, value = validate.get('extract_type'), validate.get('key'), validate.get('value')

                if (extract_type and not key) or (not extract_type and key):  # 提取数据源和变量名需同时存在或同时不存在
                    raise ValidationError(f'{row}，数据异常，请检查')
                else:  # 都设置了值，有可能是自定义函数，也有可能是自定义变量
                    pass

    def validate_validates(self, field):
        """ 校验断言信息 """
        if not self.quote_case.data:
            for index, validate in enumerate(field.data):
                row = f'断言，第【{index + 1}】行，'
                validate_type, element = validate.get('validate_type'), validate.get('element')
                data_type, value = validate.get('data_type'), validate.get('value')

                if validate_type and element and data_type and value:  # 都存在
                    self.validate_data_type_(self.func_container, row, data_type, value)  # 校验预期结果
                elif not validate_type and not element and not data_type and not value:  # 都不存在
                    continue
                else:
                    raise ValidationError(f'{row}，数据异常，请检查')

            # self.validate_base_validates(field.data, self.func_file_container)


class EditStepForm(AddStepForm):
    """ 修改步骤校验 """
    id = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_id(self, field):
        """ 校验步骤id已存在 """
        step = self.validate_data_is_exist(f'id为【{field.data}】的步骤不存在', UiStep, id=field.data)
        setattr(self, 'step', step)
