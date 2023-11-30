from pydantic import Field, field_validator

from ..model_factory import SwaggerPullLog
from apps.base_form import BaseForm, PaginationForm, required_str_field


class GetSwaggerPullListForm(PaginationForm):
    """ 查找swagger拉取记录列表form """
    project_id: int = Field(..., title='服务id')

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """

        return [SwaggerPullLog.project_id == self.project_id]


class GetSwaggerPullForm(BaseForm):
    """ 查找swagger拉取记录列表form """
    id: int = Field(..., title='数据id')

    @field_validator("id")
    def validate_id(cls, value):
        pull_log = cls.validate_data_is_exist('数据不存在', SwaggerPullLog, id=value)
        setattr(cls, "pull_log", pull_log)
        return value


class SwaggerPullForm(BaseForm):
    """ 从swagger拉取数据 """
    project_id: int = Field(..., title='服务id')
    options: list = required_str_field(title='拉取项')
