from typing import Optional

from pydantic import Field, field_validator

from apps.base_form import PaginationForm
from ..model_factory import CallBack


class GetCallBackListForm(PaginationForm):
    """ 查找回调记录列表form """
    url: Optional[str] = Field(None, title='接口地址')

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.url:
            filter_list.append(CallBack.url.like(f'%{self.url}%'))
        return filter_list


class GetCallBackForm(PaginationForm):
    """ 查找回调记录列表form """
    id: int = Field(title='回调数据id')

    @field_validator("id")
    def validate_id(cls, value):
        call_back = cls.validate_data_is_exist('数据不存在', CallBack, id=value)
        setattr(cls, "call_back", call_back)
        return value
