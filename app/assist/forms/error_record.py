# -*- coding: utf-8 -*-
from typing import Optional
from pydantic import Field, field_validator

from app.base_form import BaseForm, PaginationForm
from ..model_factory import FuncErrorRecord


class GetErrorListForm(PaginationForm):
    name: Optional[str] = Field(None, title='函数名')

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.name:
            filter_list.append(FuncErrorRecord.name.like(f'%{self.name}%'))
        return filter_list


class GetErrorForm(BaseForm):
    id: int = Field(..., title='数据id')

    @field_validator("id")
    def validate_id(cls, value):
        error_record = cls.validate_data_is_exist('数据不存在', FuncErrorRecord, id=value)
        setattr(cls, "error_record", error_record)
        return value
