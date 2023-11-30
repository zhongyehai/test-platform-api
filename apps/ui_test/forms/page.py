from typing import Optional, List

from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo

from ...base_form import BaseForm, PaginationForm, AddCaseDataForm, Field, required_str_field
from ..model_factory import WebUiPage as Page, WebUiElement as Element


class GetPageListForm(PaginationForm):
    """ 查询页面信息 """
    module_id: int = Field(..., title="模块id")
    name: Optional[str] = Field(None, title="模块名")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = [Page.module_id == self.module_id]
        if self.name:
            filter_list.append(Page.name.like(f'%{self.name}%'))
        return filter_list


class GetPageForm(BaseForm):
    """ 获取页面 """
    id: int = Field(..., title="页面id")

    @field_validator("id")
    def validate_id(cls, value):
        page = cls.validate_data_is_exist("页面不存在", Page, id=value)
        setattr(cls, "page", page)
        return value


class DeletePageForm(GetPageForm):
    """ 删除页面 """

    @field_validator("id")
    def validate_id(cls, value):
        page = Page.db.session.query(Page.create_user).filter(Page.id == value, Element.page_id == Page.id).first()
        cls.validate_is_false(page, "【页面下存在元素】 或 【页面不存在】")
        return value


class AddPageForm(BaseForm):
    """ 添加页面信息的校验 """
    project_id: int = Field(..., title="项目id")
    module_id: int = Field(..., title="模块id")
    page_list: List[AddCaseDataForm] = required_str_field(title="页面list")

    @field_validator("page_list")
    def validate_page_list(cls, value, info: ValidationInfo):
        """ 校验同一模块下页面名不重复 """
        page_list, name_list = [], []
        for index, page in enumerate(value):
            page_name = page.name
            cls.validate_is_true(f'第【{index + 1}】行，页面名必传', page_name)
            if page_name in name_list:
                raise ValueError(f'第【{index + 1}】行，与第【{name_list.index(page_name) + 1}】行，页面名重复')
            cls.validate_data_is_not_exist(
                f"当前模块下，名为【{page_name}】的页面已存在", Page, name=page_name, module_id=info.data["module_id"]
            )
            name_list.append(page.name)
            page_list.append({
                "project_id": info.data["project_id"], "module_id": info.data["module_id"], **page.model_dump()})
        return page_list


class EditPageForm(GetPageForm):
    """ 修改页面信息 """
    module_id: int = Field(..., title="模块id")
    name: str = required_str_field(title="页面名")
    desc: Optional[str] = Field(None, title="描述")

    @field_validator("name")
    def validate_name(cls, value, info: ValidationInfo):
        page = Page.query.with_entities(Page.name).filter(
            Page.module_id == info.data["module_id"], Page.id != info.data["id"], Page.name == value).first()
        cls.validate_is_false(page, f"当前模块下，名为【{value}】的页面已存在")
        return value
