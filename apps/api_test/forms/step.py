from typing import Optional, Union, List

from pydantic import Field, field_validator

from ...base_form import BaseForm, PaginationForm, ExtractModel, ValidateModel, HeaderModel, ParamModel, DataFormModel, \
    SkipIfModel, required_str_field
from ..model_factory import ApiStep as Step
from ...enums import ApiBodyTypeEnum, DataStatusEnum


class GetStepListForm(PaginationForm):
    """ 根据用例id获取步骤列表 """
    case_id: int = Field(..., title="用例id")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """

        return [Step.case_id == self.case_id]


class GetStepForm(BaseForm):
    """ 根据步骤id获取步骤 """
    id: int = Field(..., title="步骤id")

    @field_validator("id")
    def validate_id(cls, value):
        step = cls.validate_data_is_exist("步骤不存在", Step, id=value)
        setattr(cls, "step", step)
        return value


class DeleteStepForm(BaseForm):
    """ 批量删除步骤 """
    id_list: list = required_str_field(title="步骤id list")


class ChangeStepStatusForm(DeleteStepForm):
    """ 批量修改步骤状态 """
    status: DataStatusEnum = Field(..., title="步骤状态")


class CopyStepForm(GetStepForm):
    """ 复制步骤 """
    case_id: Optional[int] = Field(title="要复制到的用例id")


class AddStepForm(BaseForm):
    """ 添加步骤校验 """
    case_id: int = Field(..., title="步骤所属的用例id")
    quote_case: Optional[int] = Field(None, title="引用用例id（步骤为引用用例时必传）")
    name: str = required_str_field(title="步骤名称")
    desc: Optional[str] = Field('', title="步骤描述")
    up_func: Optional[list] = Field(default=[], title="前置条件")
    down_func: Optional[list] = Field(default=[], title="后置条件")
    skip_if: List[SkipIfModel] = required_str_field(title="跳过条件")
    run_times: int = Field(1, title="执行次数")
    extracts: List[ExtractModel] = required_str_field(title="数据提取")
    skip_on_fail: int = Field(1, title="当用例有失败的步骤时，是否跳过此步骤")
    validates: List[ValidateModel] = required_str_field(title="断言")
    data_driver: Union[list, dict] = Field([], title="数据驱动")

    api_id: Optional[int] = Field(None, title="步骤对应的接口id（步骤为接口时必传）")
    headers: List[HeaderModel] = required_str_field(title="跳过条件")
    params: List[ParamModel] = required_str_field(title="查询字符串参数")
    body_type: ApiBodyTypeEnum = Field(
        ApiBodyTypeEnum.json.value, title="请求体数据类型", description="json/form/text/urlencoded")
    data_form: List[DataFormModel] = required_str_field(title="form-data参数")
    data_json: Union[dict, list] = Field({}, title="json参数")
    data_urlencoded: Optional[dict] = Field({}, title="urlencoded")
    data_text: Optional[str] = Field('', title="字符串参数")
    replace_host: int = Field(0, title="是否使用用例所在项目的域名")
    pop_header_filed: list = Field([], title="头部参数中去除指定字段")
    time_out: int = Field(60, title="请求超时时间")
    allow_redirect: bool = Field(False, title="是否允许重定向, true/false")

    @field_validator('headers')
    def validate_headers(cls, value):
        """ 头部信息校验 """
        headers = [header.model_dump() for header in value]
        cls.validate_header_format(headers, content_title='头部信息')
        return headers

    @field_validator('params')
    def validate_params(cls, value):
        """ params信息校验 """
        params = [params.model_dump() for params in value]
        cls.validate_header_format(params, content_title='url参数')
        return params

    def depends_validate(self):
        self.validate_quote_case()
        self.validate_extracts()
        self.validate_validates()
        self.validate_data_form()

    def validate_quote_case(self):
        """ 不能自己引用自己 """
        if self.quote_case:
            self.validate_is_true(self.quote_case != self.case_id, "不能自己引用自己")

    def validate_extracts(self):
        """ 校验数据提取信息 """
        if not self.quote_case:
            extracts_value = [extracts.model_dump() for extracts in self.extracts]
            self.validate_api_extracts(extracts_value)

    def validate_validates(self):
        """ 校验断言信息 """
        if not self.quote_case:
            validates_value = [extracts.model_dump() for extracts in self.validates]
            self.validate_base_validates(validates_value)

    def validate_data_form(self):
        data_form_value = [data_form.model_dump() for data_form in self.data_form]
        if not self.quote_case and self.body_type == ApiBodyTypeEnum.form.value:
            self.validate_variable_format(data_form_value, msg_title='form-data')


class EditStepForm(GetStepForm, AddStepForm):
    """ 修改步骤校验 """
