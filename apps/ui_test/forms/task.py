from typing import Optional, Union

from pydantic import Field, field_validator
from crontab import CronTab

from ...base_form import BaseForm, PaginationForm, required_str_field
from ..model_factory import WebUiTask as Task
from ...enums import ReceiveTypeEnum, SendReportTypeEnum, TriggerTypeEnum, DataStatusEnum


class GetTaskListForm(PaginationForm):
    """ 获取任务列表 """
    project_id: int = Field(..., title="服务id")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        return [Task.project_id == self.project_id]


class GetTaskForm(BaseForm):
    """ 获取任务 """
    id: int = Field(..., title="任务id")

    @field_validator("id")
    def validate_id(cls, value):
        """ 校验id存在 """
        task = cls.validate_data_is_exist("任务不存在", Task, id=value)
        setattr(cls, "task", task)
        return value


class DeleteTaskForm(GetTaskForm):
    """ 删除任务 """

    def depends_validate(self):
        """ 删除任务时，同步删除内存中的任务"""
        old_task = getattr(self, 'task')
        setattr(self.task, 'delete_to_memory', old_task.status == 1)


class AddTaskForm(BaseForm):
    """ 添加定时任务的校验 """
    project_id: int = Field(..., title="服务id")
    suite_ids: Optional[list] = Field(title="用例集id")
    case_ids: Optional[list] = Field(title="用例id")
    env_list: list = required_str_field(title="运行环境")
    status: Optional[int] = Field(DataStatusEnum.DISABLE.value, title='任务状态')
    receive_type: ReceiveTypeEnum = Field(
        ReceiveTypeEnum.ding_ding, title="接收测试报告类型", description="ding_ding、we_chat、email")
    webhook_list: list = Field(title="接收消息机器人地址")
    email_server: Optional[str] = Field(None, title="发件邮箱服务器")
    email_to: Optional[list] = Field([], title="收件人邮箱")
    email_from: Optional[str] = Field(None, title="发件人邮箱")
    email_pwd: Optional[str] = Field(None, title="发件人邮箱密码")
    is_send: SendReportTypeEnum = Field(
        SendReportTypeEnum.on_fail.value, title="是否发送测试报告", description="not_send/always/on_fail")
    merge_notify: Optional[int] = Field(
        0, title="多个环境时，是否合并通知（只通知一次）", description="默认不合并，0不合并、1合并")
    cron: str = required_str_field(title="cron表达式")
    name: str = required_str_field(title="任务名")
    skip_holiday: int = Field(1, title="是否跳过节假日、调休日")
    conf: Optional[dict] = Field({}, title="运行配置", description="ui运行的浏览器，app运行的服务器、手机、是否重置APP")
    is_async: int = Field(default=0, title="任务的运行机制", description="0：串行，1：并行，默认0")
    call_back: Optional[Union[list, dict]] = Field(title="回调给流水线")

    @field_validator("cron")
    def validate_cron(cls, value):
        """ 校验cron格式 """
        try:
            if len(value.strip().split(" ")) == 6:
                value += " *"
            CronTab(value)
        except Exception as error:
            raise ValueError(f"时间配置【{value}】错误，需为cron格式, 请检查")
        if value.startswith("*"):  # 每秒钟
            raise ValueError(f"设置的执行频率过高，请重新设置")
        return value

    @field_validator("conf")
    def validate_conf(cls, value):
        """ 校验任务运行配置 """
        cls.validate_is_true(value.get("browser"), '请选择运行浏览器')
        return value

    def depends_validate(self):
        """ 发送报告类型 1.不发送、2.始终发送、3.仅用例不通过时发送 """
        if self.is_send in [SendReportTypeEnum.always.value, SendReportTypeEnum.on_fail.value]:
            if self.receive_type in (ReceiveTypeEnum.ding_ding.value, ReceiveTypeEnum.we_chat.value):
                self.validate_is_true(self.webhook_list, '选择了要通过机器人发送报告，则webhook地址必填')
            elif self.receive_type == ReceiveTypeEnum.email.value:
                self.validate_email(self.email_server, self.email_from, self.email_pwd, self.email_to)


class EditTaskForm(AddTaskForm, GetTaskForm):
    """ 编辑任务 """

    def depends_validate(self):
        """ 启用中 且 cron表达式有更改的，需要更新内存中的任务"""
        old_task = getattr(self, 'task')
        setattr(self.task, 'update_to_memory', old_task.status == 1 and self.cron != old_task.cron)


class RunTaskForm(GetTaskForm):
    """ 运行任务 """
    env_list: Optional[list] = Field(None, title="运行环境")
    is_async: int = Field(default=0, title="任务的运行机制", description="0：串行，1：并行，默认0")
    trigger_type: Optional[TriggerTypeEnum] = Field(
        TriggerTypeEnum.page, title="触发类型", description="pipeline/page/cron")  # pipeline 跑完过后会发送测试报告
    extend: Optional[Union[list, dict, str]] = Field(
        None, title="扩展字段", description="运维传过来的扩展字段，接收的什么就返回什么")
    browser: str = Field("chrome", title="浏览器")
