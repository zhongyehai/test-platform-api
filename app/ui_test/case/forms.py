# -*- coding: utf-8 -*-

import json

from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired

from ..project.models import UiProject, UiProjectEnv
from ..caseSet.models import UiCaeSet
from ..step.models import UiStep
from app.baseForm import BaseForm
# from ..task.models import Task
from .models import UiCase


class AddCaseForm(BaseForm):
    """ 添加用例的校验 """
    name = StringField(validators=[DataRequired('用例名称不能为空')])
    desc = StringField()
    func_files = StringField()
    variables = StringField()
    headers = StringField()
    run_times = IntegerField()
    set_id = IntegerField(validators=[DataRequired('请选择用例集')])
    steps = StringField()
    num = StringField()

    all_func_name = {}
    all_variables = {}
    project = None

    def validate_variables(self, field):
        """ 公共变量参数的校验
        1.校验是否存在引用了自定义函数但是没有引用自定义函数文件的情况
        2.校验是否存在引用了自定义变量，但是自定义变量未声明的情况
        """
        if not self.project:
            self.project = UiProject.get_first(id=UiCaeSet.get_first(id=self.set_id.data).project_id)

        env = UiProjectEnv.get_first(project_id=self.project.id).to_dict()
        setattr(self, 'project_env', env)

        # 自定义函数
        func_files = env['func_files']
        func_files.extend(self.func_files.data)
        self.validate_func(self.all_func_name, func_files, self.dumps(field.data))

        # 公共变量
        variables = env['variables']
        variables.extend(field.data)
        self.validate_variable_and_header_format(field.data, '自定义变量设置，，第【', '】行，要设置自定义变量，则key和value都需设置')
        self.validate_variable(self.all_variables, variables, self.dumps(field.data))

    def validate_headers(self, field):
        """ 头部参数的校验
        1.校验是否存在引用了自定义函数但是没有引用自定义函数文件的情况
        2.校验是否存在引用了自定义变量，但是自定义变量未声明的情况
        """
        if not self.project:
            self.project = UiProject.get_first(id=UiCaeSet.get_first(id=self.set_id.data).project_id)

        # 自定义函数
        func_files = self.project_env['func_files']
        func_files.extend(self.func_files.data)
        self.validate_func(self.all_func_name, func_files, self.dumps(field.data))

        # 公共变量
        variables = self.project_env['variables']
        variables.extend(self.variables.data)
        self.validate_variable_and_header_format(field.data, '头部信息设置，第【', '】行，要设置头部信息，则key和value都需设置')
        self.validate_variable(self.all_variables, variables, self.dumps(field.data))

    def validate_set_id(self, field):
        """ 校验用例集存在 """
        self.validate_data_is_exist(f'id为【{field.data}】的用例集不存在', UiCaeSet, id=field.data)

    def validate_name(self, field):
        """ 用例名不重复 """
        self.validate_data_is_not_exist(f'用例名【{field.data}】已存在', UiCase, name=field.data, set_id=self.set_id.data)


class EditCaseForm(AddCaseForm):
    """ 修改用例 """
    id = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_id(self, field):
        """ 校验用例id已存在 """
        old_data = self.validate_data_is_exist(f'id为【{field.data}】的用例不存在', UiCase, id=field.data)
        setattr(self, 'old_data', old_data)

    def validate_name(self, field):
        """ 同一用例集下用例名不重复 """
        self.validate_data_is_not_repeat(
            f'用例名【{field.data}】已存在',
            UiCase,
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
            case = UiCase.query.filter_by(
                set_id=self.setId.data).filter(UiCase.name.like('%{}%'.format(field.data)))
            setattr(self, 'case', case)


class DeleteCaseForm(BaseForm):
    """ 删除用例 """
    id = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_id(self, field):
        case = self.validate_data_is_exist('没有该用例', UiCase, id=field.data)
        self.validate_data_is_true(
            '不能删除别人的用例',
            UiProject.is_can_delete(UiCaeSet.get_first(id=case.set_id).project_id, case)
        )

        # 校验是否有定时任务已引用此用例
        # for task in Task.query.filter(Task.case_id.like(f'%{field.data}%')).all():
        #     if field.data in json.loads(task.case_id):
        #         raise ValidationError(f'定时任务【{task.name}】已引用此用例，请先解除引用')

        # 校验是否有其他用例已引用此用例
        step = UiStep.get_first(quote_case=field.data)
        if step:
            raise ValidationError(f'用例【{UiCase.get_first(id=step.case_id).name}】已引用此用例，请先解除引用')

        setattr(self, 'case', case)


class GetCaseForm(BaseForm):
    """ 获取用例信息 """
    id = IntegerField(validators=[DataRequired('用例id必传')])
    env = StringField()

    def validate_id(self, field):
        case = self.validate_data_is_exist(f'id为【{field.data}】的用例不存在', UiCase, id=field.data)
        setattr(self, 'case', case)


class RunCaseForm(BaseForm):
    """ 运行用例 """
    caseId = StringField(validators=[DataRequired('请选择用例')])
    env = StringField(validators=[DataRequired('请选择运行环境')])

    def validate_caseId(self, field):
        """ 校验用例id存在 """
        case = self.validate_data_is_exist(f'id为【{field.data}】的用例不存在', UiCase, id=field.data)
        setattr(self, 'case', case)
