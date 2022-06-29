# -*- coding: utf-8 -*-
import json

from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired

from ..func.models import Func
from ..project.models import ApiProject, ApiProjectEnv
from ..sets.models import ApiSet
from ..step.models import ApiStep as Step
from app.baseForm import BaseForm
from ..task.models import ApiTask
from .models import ApiCase


class GetCaseForm(BaseForm):
    """ 获取用例信息 """
    id = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_id(self, field):
        case = self.validate_data_is_exist(f'id为【{field.data}】的用例不存在', ApiCase, id=field.data)
        setattr(self, 'case', case)


class AddCaseForm(BaseForm):
    """ 添加用例的校验 """
    set_id = IntegerField(validators=[DataRequired('请选择用例集')])
    name = StringField(validators=[DataRequired('用例名称不能为空')])
    func_files = StringField()
    variables = StringField()
    headers = StringField()
    run_times = IntegerField()
    steps = StringField()
    num = StringField()
    desc = StringField()

    all_func_name = {}
    all_variables = {}
    project = None
    project_env = None

    def validate_set_id(self, field):
        """ 校验用例集存在 """
        self.validate_data_is_exist(f'id为【{field.data}】的用例集不存在', ApiSet, id=field.data)
        self.project = ApiProject.get_first(id=ApiSet.get_first(id=self.set_id.data).project_id)
        self.project_env = ApiProjectEnv.get_first(project_id=self.project.id).to_dict()

    def validate_func_files(self, field):
        """ 合并项目选择的自定义函数和用例选择的自定义函数文件 """
        func_files = self.project_env['func_files']
        func_files.extend(field.data)
        self.all_func_name = Func.get_func_by_func_file_name(func_files)

    def validate_variables(self, field):
        """ 公共变量参数的校验
        1.校验是否存在引用了自定义函数但是没有引用自定义函数文件的情况
        2.校验是否存在引用了自定义变量，但是自定义变量未声明的情况
        """
        # 校验格式
        self.validate_variable_and_header_format(field.data, '自定义变量设置，，第【', '】行，要设置自定义变量，则key和value都需设置')

        # 校验引用的自定义函数
        self.validate_func(self.all_func_name, content=self.dumps(field.data))

        # 公共变量引用项目设置的变量
        variables = self.project_env['variables']
        variables.extend(field.data)
        self.all_variables = {
            variable.get('key'): variable.get('value') for variable in variables if variable.get('key')
        }
        # 校验变量
        self.validate_variable(self.all_variables, self.dumps(field.data))

    def validate_headers(self, field):
        """ 头部参数的校验
        1.校验是否存在引用了自定义函数但是没有引用自定义函数文件的情况
        2.校验是否存在引用了自定义变量，但是自定义变量未声明的情况
        """
        # 校验格式
        self.validate_variable_and_header_format(field.data, '自定义变量设置，，第【', '】行，要设置自定义变量，则key和value都需设置')

        # 校验引用的自定义函数
        self.validate_func(self.all_func_name, content=self.dumps(field.data))

        # 校验引用的变量
        self.validate_variable(self.all_variables, self.dumps(field.data))

    def validate_name(self, field):
        """ 用例名不重复 """
        self.validate_data_is_not_exist(f'用例名【{field.data}】已存在', ApiCase, name=field.data, set_id=self.set_id.data)


class EditCaseForm(GetCaseForm, AddCaseForm):
    """ 修改用例 """

    def validate_name(self, field):
        """ 同一用例集下用例名不重复 """
        self.validate_data_is_not_repeat(
            f'用例名【{field.data}】已存在',
            ApiCase,
            self.id.data,
            name=field.data,
            set_id=self.set_id.data
        )


class FindCaseForm(BaseForm):
    """ 根据用例集查找用例 """
    name = StringField()
    setId = IntegerField(validators=[DataRequired('请选择用例集')])
    pageNum = IntegerField()
    pageSize = IntegerField()

    def validate_name(self, field):
        if field.data:
            case = ApiCase.query.filter_by(
                set_id=self.setId.data).filter(ApiCase.name.like('%{}%'.format(field.data)))
            setattr(self, 'case', case)


class DeleteCaseForm(BaseForm):
    """ 删除用例 """
    id = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_id(self, field):
        case = self.validate_data_is_exist('用例不存在', ApiCase, id=field.data)

        self.validate_data_is_true(
            f'不能删除别人的用例',
            ApiProject.is_can_delete(ApiSet.get_first(id=case.set_id).project_id, case)
        )

        # 校验是否有定时任务已引用此用例
        for task in ApiTask.query.filter(ApiTask.case_id.like(f'%{field.data}%')).all():
            self.validate_data_is_false(f'定时任务【{task.name}】已引用此用例，请先解除引用', field.data in json.loads(task.case_id))

        # 校验是否有其他用例已引用此用例
        step = Step.get_first(quote_case=field.data)
        if step:
            raise ValidationError(f'用例【{ApiCase.get_first(id=step.case_id).name}】已引用此用例，请先解除引用')

        setattr(self, 'case', case)


class RunCaseForm(BaseForm):
    """ 运行用例 """
    caseId = StringField(validators=[DataRequired('请选择用例')])
    env = StringField(validators=[DataRequired('请选择运行环境')])

    def validate_caseId(self, field):
        """ 校验用例id存在 """
        self.validate_data_is_true('用例id必传', self.caseId.data)

        case_list = []
        for case_id in self.caseId.data:
            case_list.append(self.validate_data_is_exist(f'id为【{case_id}】的用例不存在', ApiCase, id=case_id))
        setattr(self, 'case_list', case_list)
