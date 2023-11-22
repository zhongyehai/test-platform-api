from typing import Optional
from pydantic import Field

from app.base_form import BaseForm, PaginationForm


class GetFileListForm(PaginationForm):
    """ 获取文件列表 """
    file_type: Optional[str] = Field(default="case", title='文件类型')


class CheckFileIsExistsForm(BaseForm):
    """ 校验文件是否存在 """
    file_name: str = Field(..., title='文件名')
    file_type: str = Field(..., title='文件类型')
