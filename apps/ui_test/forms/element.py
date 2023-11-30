# -*- coding: utf-8 -*-
from typing import Optional, List

from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo

from ...base_form import BaseForm, PaginationForm, Field, AddElementDataForm, required_str_field
from ..model_factory import WebUiElement as Element, WebUiPage as Page, WebUiModule as Module, WebUiProject as Project, \
    WebUiStep as Step, WebUiCase as Case


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

    @field_validator("element_list")
    def validate_element_list(cls, value, info: ValidationInfo):
        """ 校验元素信息 """
        addr_lit, name_list, element_list = [], [], []
        for index, element_form in enumerate(value):
            cls.validate_is_true(element_form.name, f'第【{index + 1}】行，元素名必传')
            cls.validate_is_true(element_form.by, f'第【{index + 1}】行，定位方式必传')
            cls.validate_is_true(element_form.element, f'第【{index + 1}】行，元素表达式必传')
            if element_form.name in name_list:
                raise ValueError(f'第【{index + 1}】行，与第【{name_list.index(element_form.name) + 1}】行，元素名重复')
            cls.validate_data_is_not_exist(
                f'第【{index + 1}】行，当前页面下，名为【{element_form.name}】的元素已存在',
                Element, name=element_form.name, page_id=info.data["page_id"]
            )
            if element_form.by == "url":
                addr_lit.append(element_form.element)
            element_dict = element_form.model_dump()
            element_dict.pop("template_device")
            element_list.append({
                "project_id": info.data["project_id"],
                "module_id": info.data["module_id"],
                "page_id": info.data["page_id"],
                **element_dict
            })
        setattr(cls, 'addr_lit', addr_lit)
        return element_list

    def update_page_addr(self):
        """ 如果元素是页面地址，则同步修改页面表里面对应的地址 """
        if len(self.addr_lit) > 0:
            Page.query.filter_by(id=self.page_id).update({"addr": self.addr_lit[0]})


class EditElementForm(BaseForm):
    """ 修改元素信息 """
    id: int = Field(..., title="元素id")
    page_id: int = Field(..., title="页面id")
    name: str = required_str_field(title="元素名")
    element: str = required_str_field(title="定位元素表达式")
    desc: Optional[str] = Field(title="备注")
    wait_time_out: Optional[int] = Field(title="等待超时时间")
    by: str = required_str_field(title="定位方式")

    @field_validator("name")
    def validate_name(cls, value, info: ValidationInfo):
        """ 校验元素名不重复 """
        cls.validate_data_is_not_repeat(
            f"当前页面下，名为【{value}】的元素已存在",
            Element, info.data["id"], name=value, page_id=info.data["page_id"]
        )
        return value

    @field_validator("by")
    def validate_by(cls, value, info: ValidationInfo):
        if value == "url":
            cls.validate_data_is_not_repeat(
                f"一个页面只能有一个地址", Element, info.data["id"], page_id=info.data["page_id"], by="url")
            setattr(cls, 'addr_lit', [info.data["element"]])
        # 如果是坐标定位，校验坐标值
        elif value in ("coordinate", "bounds"):
            if value == "bounds":
                cls.validate_is_true(f'请选择元素定位时参照的设备', info.data["template_device"])
            try:
                if isinstance(eval(info.data["element"]), (tuple, list)) is False:
                    raise ValueError("元素表达式错误，请参照示例填写")
            except:
                raise ValueError("元素表达式错误，请参照示例填写")
        return value

    def update_page_addr(self):
        """ 如果元素是页面地址，则同步修改页面表里面对应的地址 """
        if hasattr(self, 'addr_lit') and len(self.addr_lit) > 0:
            Page.query.filter_by(id=self.page_id).update({"addr": self.addr_lit[0]})


class ChangeElementByIdForm(BaseForm):
    """ 根据id更新元素 """
    id: int = Field(..., title="元素id")
    by: str = required_str_field(title="定位方式")
    element: str = required_str_field(title="定位元素表达式")
