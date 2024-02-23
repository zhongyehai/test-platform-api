from typing import Optional, List

from pydantic import field_validator

from ...base_form import BaseForm, Field, PaginationForm, AddCaseDataForm, VariablesModel, SkipIfModel, \
    required_str_field
from ..model_factory import WebUiProject as Project, WebUiProjectEnv as ProjectEnv, WebUiCaseSuite as CaseSuite, \
    WebUiStep as Step, WebUiCase as Case
from ...assist.models.script import Script
from ...enums import CaseStatusEnum


class GetCaseListForm(PaginationForm):
    """ 获取用例列表 """
    name: Optional[str] = Field(None, title="用例名")
    status: Optional[int] = Field(
        None, title="用例调试状态",
        description="0未调试-不执行，1调试通过-要执行，2调试通过-不执行，3调试不通过-不执行，默认未调试-不执行")
    has_step: Optional[bool] = Field(False, title="结果中是否标识用例下是否有步骤")
    suite_id: int = Field(..., title="用例集")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = [Case.suite_id == self.suite_id]
        if self.name:
            filter_list.append(Case.name.like(f'%{self.name}%'))
        if self.status:
            filter_list.append(Case.status == self.status)
        return filter_list


class GetAssistCaseForm(BaseForm):
    """ 根据服务查找用例 """
    project_id: int = Field(..., title="服务id")


class GetCaseNameForm(BaseForm):
    """ 获取用例的名字 """
    case_list: List[int] = required_str_field(title="用例id list")


class GetCaseForm(BaseForm):
    """ 获取用例信息 """
    id: int = Field(..., title="用例id")

    @field_validator("id")
    def validate_id(cls, value):
        case = cls.validate_data_is_exist("用例不存在", Case, id=value)
        setattr(cls, "case", case)
        return value


class DeleteCaseForm(BaseForm):
    """ 删除用例 """
    id_list: List = required_str_field(title="用例id list")

    @field_validator("id_list")
    def validate_id_list(cls, value):
        # 校验是否有其他用例已引用此用例
        case_name = Case.db.session.query(Case.name).filter(Step.quote_case.in_(value), Step.case_id == Case.id).first()
        if case_name:
            raise ValueError(f"用例【{case_name}】已引用此用例为步骤，请先解除引用")
        return value


class ChangeCaseStatusForm(BaseForm):
    """ 批量修改用例状态 """
    id_list: List[int] = required_str_field(title="用例id list")
    status: CaseStatusEnum = Field(
        ..., title="用例调试状态",
        description="0未调试-不执行，1调试通过-要执行，2调试通过-不执行，3调试不通过-不执行，默认未调试-不执行")


class CopyCaseStepForm(BaseForm):
    """ 复制用例的步骤 """

    from_case: int = Field(..., title="复制源用例id")
    to_case: int = Field(..., title="当前用例id")

    def depends_validate(self):
        if self.from_case != self.to_case:
            self.validate_is_true(
                len(Case.query.filter(Case.id.in_([self.from_case, self.to_case])).all()) == 2, "用例不存在")


class PullCaseStepForm(BaseForm):
    """ 拉取当前引用用例的步骤到当前步骤所在的位置 """
    step_id: int = Field(..., title="复制源步骤id")
    case_id: int = Field(..., title="用例id")

    @field_validator('step_id')
    def validate_step_id(cls, value):
        step = cls.validate_data_is_exist("步骤不存在", Step, id=value)
        setattr(cls, 'step', step)
        return value

    @field_validator('case_id')
    def validate_case_id(cls, value):
        case = cls.validate_data_is_exist("用例不存在不存在", Case, id=value)
        setattr(cls, 'case', case)
        return value


class AddCaseForm(BaseForm):
    """ 添加用例的校验 """
    suite_id: int = Field(..., title="用例集id")
    case_list: List[AddCaseDataForm] = required_str_field(title="用例")

    def depends_validate(self):
        case_data_list = []
        for index, case in enumerate(self.case_list):
            case_data_list.append({"suite_id": self.suite_id, **case.model_dump()})  # 保存用例数据，并加上用例集id
        self.case_list = case_data_list


class EditCaseForm(GetCaseForm):
    """ 修改用例 """
    suite_id: int = Field(..., title="用例集id")
    name: str = required_str_field(title="用例名称")
    desc: str = required_str_field(title="用例描述")
    script_list: List[int] = Field(default=[], title="引用脚本id")
    skip_if: List[SkipIfModel] = required_str_field(title="跳过条件")
    variables: List[VariablesModel] = required_str_field(title="变量")
    run_times: int = Field(1, title="运行次数")

    def depends_validate(self):
        self.validate_suite_id()
        self.validate_script_list()
        self.validate_variables()

    def validate_suite_id(self):
        project = Project.query.filter(CaseSuite.id == self.suite_id, Project.id == CaseSuite.project_id).first()
        self.validate_is_true(project, "用例集不存在")
        project_env = ProjectEnv.query.filter_by(project_id=project.id).first()
        setattr(self, 'project', project)
        setattr(self, 'project_env', project_env)

    def validate_script_list(self):
        # 合并项目选择的自定义函数和用例选择的脚本文件
        all_script_list = getattr(self, 'project').script_list
        all_script_list.extend(self.script_list)
        all_func_name = Script.get_func_by_script_id(all_script_list)
        setattr(self, 'all_func_name', all_func_name)

    def validate_variables(self):
        # 合并环境的变量和case的变量
        variables = getattr(self, 'project_env').variables
        current_variables = [variable.model_dump() for variable in self.variables]
        variables.extend(current_variables)
        all_variables = {variable.get("key"): variable.get("value") for variable in variables if variable.get("key")}
        setattr(self, 'all_variables', all_variables)

        # 1.校验是否存在引用了自定义函数但是没有引用脚本文件的情况
        # 2.校验是否存在引用了自定义变量，但是自定义变量未声明的情况
        self.validate_variable_format(current_variables)  # 校验格式
        self.validate_func(getattr(self, 'all_func_name'), content=self.dumps(current_variables))  # 校验引用的自定义函数
        self.validate_variable(all_variables, self.dumps(current_variables), "自定义变量")  # 校验变量


class RunCaseForm(BaseForm):
    """ 运行用例 """
    case_id_list: List[int] = required_str_field(title="用例id list")
    env_list: List[str] = required_str_field(title="运行环境code")
    temp_variables: Optional[dict] = Field(title="临时指定参数")
    is_async: int = Field(default=0, title="执行模式", description="0：用例维度串行执行，1：用例维度并行执行")
    browser: str = Field("chrome", title="浏览器")

    def depends_validate(self):
        """ 公共变量参数的校验
        1.校验是否存在引用了自定义函数但是没有引用脚本文件的情况
        2.校验是否存在引用了自定义变量，但是自定义变量未声明的情况
        """
        if self.temp_variables and len(self.case_id_list) == 1:
            variables = self.temp_variables.get("variables", [])

            # 1、先校验数据格式
            if len(variables) > 0:  # 校验变量
                self.validate_variable_format(variables)  # 校验格式

            # 2、校验数据引用是否合法
            suite_id, case_script_list = Case.db.session.query(
                Case.suite_id, Case.script_list).filter(Case.id == self.case_id_list[0]).first()
            project = Project.query.filter(CaseSuite.id == suite_id, Project.id == CaseSuite.project_id).first()

            # 自定义函数
            project_script_id_list = project.script_list
            project_script_id_list.extend(case_script_list)
            all_func_name = Script.get_func_by_script_id(project_script_id_list)
            self.validate_func(all_func_name, content=self.dumps(variables))  # 校验引用的自定义函数

            # 变量
            env_variables = ProjectEnv.get_first(project_id=project.id).variables
            env_variables.extend(variables)
            all_variables = {
                variable.get("key"): variable.get("value") for variable in env_variables if variable.get("key")
            }
            if len(variables) > 0:  # 校验变量
                self.validate_variable(all_variables, self.dumps(variables), "自定义变量")  # 校验变量
