from typing import Optional, Union, List

from pydantic import Field, field_validator

from ...base_form import BaseForm, PaginationForm, ExtractModel, ValidateModel, SkipIfModel, required_str_field
from ..model_factory import WebUiStep as Step
from ...enums import DataStatusEnum


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
    up_func: Optional[list] = Field(default=[], title="前置条件")
    down_func: Optional[list] = Field(default=[], title="后置条件")
    skip_if: List[SkipIfModel] = required_str_field(title="跳过条件")
    run_times: int = Field(1, title="执行次数")
    extracts: List[ExtractModel] = required_str_field(title="数据提取")
    skip_on_fail: int = Field(1, title="当用例有失败的步骤时，是否跳过此步骤")
    validates: List[ValidateModel] = required_str_field(title="断言")
    data_driver: Union[list, dict] = Field([], title="数据驱动")

    element_id: Optional[int] = Field(None, title="步骤对应的元素id")
    send_keys: str = Field(None, title="输入内容")
    execute_type: Optional[str] = Field('', title="执行动作")
    wait_time_out: int = Field(5, title="等待元素超时时间")

    def depends_validate(self):
        self.validate_quote_case()
        self.validate_extracts()
        self.validate_validates()
        self.validate_execute_type()

    def validate_quote_case(self):
        """ 不能自己引用自己 """
        if self.quote_case:
            self.validate_is_true(self.quote_case != self.case_id, "不能自己引用自己")

    def validate_extracts(self):
        """ 校验数据提取信息 """
        if not self.quote_case:
            extracts_value = [extracts.model_dump() for extracts in self.extracts]
            self.validate_ui_extracts(extracts_value)

    def validate_validates(self):
        """ 校验断言信息 """
        if not self.quote_case:
            validates_value = [extracts.model_dump() for extracts in self.validates]
            self.validate_base_validates(validates_value)

    def validate_execute_type(self):
        """ 如果不是引用用例，则执行方式不能为空 """
        if not self.quote_case:
            if not self.execute_type:
                raise ValueError("执行方式不能为空")
            if "dict" in self.execute_type:  # 校验输入字典的项能不能序列化和反序列化
                send_keys = self.send_keys
                try:
                    self.loads(send_keys)
                except Exception as error:
                    raise ValueError(f"【{send_keys}】不能转为json，请确认")


class EditStepForm(GetStepForm, AddStepForm):
    """ 修改步骤校验 """
