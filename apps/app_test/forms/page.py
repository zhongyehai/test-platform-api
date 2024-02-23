from typing import Optional, List

from pydantic import field_validator

from ...base_form import BaseForm, PaginationForm, AddCaseDataForm, Field, required_str_field
from ..model_factory import AppUiPage as Page, AppUiElement as Element


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

    def depends_validate(self):
        page_data_list = []
        for index, page in enumerate(self.page_list):
            page_data_list.append({"project_id": self.project_id, "module_id": self.module_id, **page.model_dump()})
        self.page_list = page_data_list


class EditPageForm(GetPageForm):
    """ 修改页面信息 """
    module_id: int = Field(..., title="模块id")
    name: str = required_str_field(title="页面名")
    desc: Optional[str] = Field(None, title="描述")
