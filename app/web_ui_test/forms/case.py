# -*- coding: utf-8 -*-
import json

from wtforms import StringField, IntegerField, BooleanField
from wtforms.validators import ValidationError, DataRequired, Length

from app.assist.models.script import Script
from app.web_ui_test.models.project import WebUiProject as Project, WebUiProjectEnv as ProjectEnv
from app.web_ui_test.models.caseSuite import WebUiCaseSuite as CaseSuite
from app.web_ui_test.models.step import WebUiStep as Step
from app.baseForm import BaseForm
from app.web_ui_test.models.task import WebUiTask as Task
from app.web_ui_test.models.case import WebUiCase as Case


class GetCaseForm(BaseForm):
    """ 获取用例信息 """
    id = IntegerField(validators=[DataRequired("用例id必传")])

    def validate_id(self, field):
        case = self.validate_data_is_exist(f"id为【{field.data}】的用例不存在", Case, id=field.data)
        setattr(self, "case", case)


class ChangeCaseStatusForm(BaseForm):
    """ 批量修改用例状态 """
    id = StringField(validators=[DataRequired("用例id必传")])
    status = StringField()

    def validate_id(self, field):
        case_list = []
        for case_id in field.data:
            case = Case.get_first(id=case_id)
            if case:
                case_list.append(case)
        setattr(self, "case_list", case_list)


class AddCaseForm(BaseForm):
    """ 添加用例的校验 """
    name_length = Case.name.property.columns[0].type.length
    suite_id = IntegerField(validators=[DataRequired("请选择用例集")])
    case_list = StringField(validators=[DataRequired("用例必填")])

    project = {}
    project_env = {}

    def validate_suite_id(self, field):
        """ 校验用例集存在 """
        self.validate_data_is_exist(f"id为【{field.data}】的用例集不存在", CaseSuite, id=field.data)
        self.project = Project.get_first(id=CaseSuite.get_first(id=self.suite_id.data).project_id).to_dict()
        self.project_env = ProjectEnv.get_first(project_id=self.project["id"]).to_dict()

    def validate_case_list(self, field):
        """ 用例名不重复 """
        name_list = []
        for index, case in enumerate(field.data):
            case_name, desc = case.get("name"), case.get("desc")
            self.validate_data_is_true(f'第【{index + 1}】行，用例名必传', case_name)
            self.validate_data_is_true(f'第【{index + 1}】行，用例名长度不可超过{self.name_length}位', case_name)
            if case_name in name_list:
                raise ValidationError(f'第【{index + 1}】行，与第【{name_list.index(case_name) + 1}】行，用例名重复')
            self.validate_data_is_true(f'第【{index + 1}】行，用例描述必传', desc)
            self.validate_data_is_not_exist(
                f'第【{index + 1}】行，用例名【{case_name}】已存在',
                Case,
                name=case_name,
                suite_id=self.suite_id.data)
            name_list.append(case_name)


class EditCaseForm(GetCaseForm, AddCaseForm):
    """ 修改用例 """
    case_list = None
    name_length = Case.name.property.columns[0].type.length
    name = StringField(validators=[
        DataRequired("用例名称不能为空"),
        Length(1, name_length, f"用例名长度不可超过{name_length}位")
    ])
    desc = StringField(validators=[DataRequired("用例描述必填")])
    script_list = StringField()
    skip_if = StringField()
    variables = StringField()
    run_times = IntegerField()
    steps = StringField()

    all_func_name = {}
    all_variables = {}

    def validate_name(self, field):
        """ 同一用例集下用例名不重复 """
        self.validate_data_is_not_repeat(
            f"用例名【{field.data}】已存在",
            Case,
            self.id.data,
            name=field.data,
            suite_id=self.suite_id.data
        )

    def merge_variables(self):
        """ 合并环境的变量和case的变量 """
        if self.all_variables.__len__() == 0:
            variables = self.project_env["variables"]
            variables.extend(self.variables.data)
            self.all_variables = {
                variable.get("key"): variable.get("value") for variable in variables if variable.get("key")
            }

    def validate_script_list(self, field):
        """ 合并项目选择的自定义函数和用例选择的脚本文件 """
        project_script_list = self.project["script_list"]
        project_script_list.extend(field.data)
        self.all_func_name = Script.get_func_by_script_name(project_script_list)

    def validate_variables(self, field):
        """ 公共变量参数的校验
        1.校验是否存在引用了自定义函数但是没有引用脚本文件的情况
        2.校验是否存在引用了自定义变量，但是自定义变量未声明的情况
        """
        self.validate_variable_format(field.data)  # 校验格式
        self.validate_func(self.all_func_name, content=self.dumps(field.data))  # 校验引用的自定义函数
        self.merge_variables()
        self.validate_variable(self.all_variables, self.dumps(field.data), "自定义变量")  # 校验变量


class FindCaseForm(BaseForm):
    """ 根据用例集查找用例 """
    name = StringField()
    status = StringField()
    getHasStep = BooleanField()
    suiteId = IntegerField(validators=[DataRequired("请选择用例集")])
    pageNum = IntegerField()
    pageSize = IntegerField()

    def validate_name(self, field):
        if field.data:
            case = Case.query.filter_by(
                suite_id=self.suiteId.data).filter(Case.name.like("%{}%".format(field.data)))
            setattr(self, "case", case)


class DeleteCaseForm(BaseForm):
    """ 删除用例 """
    id = StringField(validators=[DataRequired("用例id必传")])

    def validate_id(self, field):
        for case_id in field.data:  # TODO 批量删除用例
            case = self.validate_data_is_exist("用例不存在", Case, id=case_id)

            self.validate_data_is_true(
                f"不能删除别人的用例",
                Project.is_can_delete(CaseSuite.get_first(id=case.suite_id).project_id, case)
            )

            # 校验是否有定时任务已引用此用例
            # for task in Task.query.filter(Task.case_ids.like(f"%{field.data}%")).all():
            #     self.validate_data_is_false(
            #         f"定时任务【{task.name}】已引用此用例，请先解除引用",
            #         field.data in json.loads(task.case_ids)
            #     )

            # 校验是否有其他用例已引用此用例
            step = Step.get_first(quote_case=field.data)
            if step:
                raise ValidationError(f"用例【{Case.get_first(id=step.case_id).name}】已引用此用例，请先解除引用")

            setattr(self, "case", case)


class GetCaseForm(BaseForm):
    """ 获取用例信息 """
    id = IntegerField(validators=[DataRequired("用例id必传")])
    env = StringField()

    def validate_id(self, field):
        case = self.validate_data_is_exist(f"id为【{field.data}】的用例不存在", Case, id=field.data)
        setattr(self, "case", case)


class CopyCaseStepForm(BaseForm):
    """ 复制用例的步骤 """

    source = IntegerField(validators=[DataRequired("复制源用例id必传")])
    to = IntegerField(validators=[DataRequired("当前用例id必传")])

    def validate_source(self, field):
        source_case = self.validate_data_is_exist(f"id为【{field.data}】的用例不存在", Case, id=field.data)
        setattr(self, "source_case", source_case)

    def validate_to(self, field):
        to_case = self.validate_data_is_exist(f"id为【{field.data}】的用例不存在", Case, id=field.data)
        setattr(self, "to_case", to_case)


class PullCaseStepForm(BaseForm):
    """ 拉取当前引用用例的步骤到当前步骤所在的位置 """
    current = IntegerField(validators=[DataRequired("复制源步骤id必传")])
    caseId = IntegerField()

    def validate_current(self, field):
        current_step = self.validate_data_is_exist(f"id为【{field.data}】的步骤不存在", Step, id=field.data)
        setattr(self, "current_step", current_step)


class RunCaseForm(BaseForm):
    """ 运行用例 """
    caseId = StringField(validators=[DataRequired("请选择用例")])
    env_list = StringField(validators=[DataRequired("请选择运行环境")])
    browser = StringField(validators=[DataRequired("请选择运行浏览器")])
    temp_variables = StringField()  # 临时指定参数
    is_async = IntegerField()

    def validate_caseId(self, field):
        """ 校验用例id存在 """
        case_list = []
        for case_id in self.caseId.data:
            case_list.append(self.validate_data_is_exist(f"id为【{case_id}】的用例不存在", Case, id=case_id))
        setattr(self, "case_list", case_list)

    def validate_temp_variables(self, field):
        """ 公共变量参数的校验
        1.校验是否存在引用了自定义函数但是没有引用脚本文件的情况
        2.校验是否存在引用了自定义变量，但是自定义变量未声明的情况
        """
        if field.data and len(self.caseId.data) == 1:
            variables, headers = field.data.get("variables", []), field.data.get("headers", [])
            # 1、先校验数据格式
            if len(variables) > 0:  # 校验变量
                self.validate_variable_format(variables)  # 校验格式

            if len(headers) > 0:  # 校验头部参数
                self.validate_header_format(headers)  # 校验格式

            # 2、校验数据引用是否合法
            case = Case.get_first(id=self.caseId.data[0])
            suite = CaseSuite.get_first(id=case.suite_id)
            project = Project.get_first(id=suite.project_id)

            # 自定义函数
            project_script_list = self.loads(project.script_list)
            project_script_list.extend(self.loads(case.script_list))
            all_func_name = Script.get_func_by_script_name(project_script_list)
            self.validate_func(all_func_name, content=self.dumps(variables))  # 校验引用的自定义函数

            # 变量
            env_variables = self.loads(ProjectEnv.get_first(project_id=project.id).variables)
            env_variables.extend(self.loads(case.variables))
            all_variables = {
                variable.get("key"): variable.get("value") for variable in env_variables if variable.get("key")
            }
            if len(variables) > 0:  # 校验变量
                self.validate_variable(all_variables, self.dumps(variables), "自定义变量")  # 校验变量

            if len(headers) > 0:  # 校验头部参数
                self.validate_func(all_func_name, content=self.dumps(headers))  # 校验引用的自定义函数
                self.validate_variable(all_variables, self.dumps(headers), "头部信息")  # 校验引用的变量
