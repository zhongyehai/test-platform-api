from typing import Optional

from pydantic import Field, field_validator

from ...base_form import BaseForm, PaginationForm
from ..model_factory import SystemErrorRecord


class GetSystemErrorRecordListForm(PaginationForm):
    url: Optional[str] = Field(None, title="请求地址")
    method: Optional[str] = Field(None, title="请求方法")
    request_user: Optional[str] = Field(None, title="发起请求用户")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.url:
            filter_list.append(SystemErrorRecord.url.like(f'%{self.url}%'))
        if self.method:
            filter_list.append(SystemErrorRecord.method == self.method)
        if self.request_user:
            filter_list.append(SystemErrorRecord.request_user == self.request_user)

        return filter_list


class GetSystemErrorRecordForm(BaseForm):
    id: int = Field(..., title="数据id")

    @field_validator("id")
    def validate_id(cls, value):
        error_record = cls.validate_data_is_exist("数据不存在", SystemErrorRecord, id=value)
        setattr(cls, "error_record", error_record)
        return value
