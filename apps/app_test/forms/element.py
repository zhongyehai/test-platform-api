# -*- coding: utf-8 -*-
from typing import Optional, List

from pydantic import field_validator

from ...base_form import BaseForm, PaginationForm, Field, AddElementDataForm, required_str_field
from ..model_factory import AppUiElement as Element, AppUiStep as Step, AppUiCase as Case


class GetElementListForm(PaginationForm):
    """ 查询元素信息 """
    page_id: int = Field(..., title="页面id")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        return [Element.page_id == self.page_id]


class GetElementForm(BaseForm):
    """ 获取元素 """
    id: int = Field(..., title="元素id")

    @field_validator("id")
    def validate_id(cls, value):
        element = cls.validate_data_is_exist("元素不存在", Element, id=value)
        setattr(cls, "element", element)
        return value


class DeleteElementForm(GetElementForm):
    """ 删除元素 """

    @field_validator("id")
    def validate_id(cls, value):
        case_name = Case.db.session.query(Case.name).filter(Step.element_id == value, Case.id == Step.case_id).first()
        cls.validate_is_false(case_name, f'用例【{case_name}】已经使用此步骤，请先解除引用')
        return value


class AddElementForm(BaseForm):
    """ 添加元素信息的校验 """
    project_id: int = Field(..., title="APP id")
    module_id: int = Field(..., title="模块id")
    page_id: int = Field(..., title="页面id")
    element_list: List[AddElementDataForm] = required_str_field(title="元素list")

    def depends_validate(self):
        element_data_list = []
        for index, element in enumerate(self.element_list):
            if element.by in ("coordinate", "bounds"):
                if element.by == "bounds":
                    self.validate_is_true(element.template_device, f'第【{index + 1}】行，请选择定位时参照的设备')
                try:
                    if isinstance(eval(element.element), (tuple, list)) is False:
                        raise ValueError(f'第【{index + 1}】行，元素表达式错误，请参照示例填写')
                except:
                    raise ValueError(f'第【{index + 1}】行，元素表达式错误，请参照示例填写')
            element_data_list.append({
                "project_id": self.project_id,
                "module_id": self.module_id,
                "page_id": self.page_id,
                **element.model_dump()
            })
        self.element_list = element_data_list


class EditElementForm(BaseForm):
    """ 修改元素信息 """
    id: int = Field(..., title="元素id")
    page_id: int = Field(..., title="页面id")
    name: str = required_str_field(title="元素名")
    element: str = required_str_field(title="定位元素表达式")
    template_device: Optional[int] = Field(title="元素定位时参照的设备")
    desc: Optional[str] = Field(title="备注")
    wait_time_out: Optional[int] = Field(title="等待超时时间")
    by: str = required_str_field(title="定位方式")

    def depends_validate(self):
        if self.by in ("coordinate", "bounds"):
            if self.by == "bounds":
                self.validate_is_true(self.template_device, f'请选择元素定位时参照的设备')
            try:
                if isinstance(eval(self.element), (tuple, list)) is False:
                    raise ValueError("元素表达式错误，请参照示例填写")
            except:
                raise ValueError("元素表达式错误，请参照示例填写")


class ChangeElementByIdForm(BaseForm):
    """ 根据id更新元素 """
    id: int = Field(..., title="元素id")
    by: str = required_str_field(title="定位方式")
    element: str = required_str_field(title="定位元素表达式")
