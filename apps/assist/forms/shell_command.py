from pydantic import Field, field_validator

from ..model_factory import ShellCommandRecord
from apps.base_form import BaseForm, PaginationForm, required_str_field


class GetShellCommandRecordListForm(PaginationForm):
    """ 获取shell命令发送记录列表 """
    command: str = Field(..., title='shell命令')

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        return [ShellCommandRecord.command == self.command]


class GetShellCommandRecordForm(BaseForm):
    """ 获取shell命令发送记录 """
    id: int = Field(..., title='数据id')

    @field_validator("id")
    def validate_id(cls, value):
        shell_command_log = cls.validate_data_is_exist('数据不存在', ShellCommandRecord, id=value)
        setattr(cls, "shell_command_log", shell_command_log)
        return value


class SendShellCommandForm(BaseForm):
    """ 发送shell命令 """
    file_content: str = required_str_field(title='文件数据')
    command: str = required_str_field(title='shell命令')
