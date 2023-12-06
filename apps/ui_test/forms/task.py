from typing import Optional, Union

from pydantic import Field, field_validator, ValidationInfo
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

    @field_validator("id")
    def validate_id(cls, value):
        """ 校验id存在 """
        task = cls.validate_data_is_exist("任务不存在", Task, id=value)
        cls.validate_is_true(task.is_disable(), "请先禁用任务")
        setattr(cls, "task", task)
        return value


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
    email_server: Optional[str] = Field(title="发件邮箱服务器")
    email_to: list = Field(title="收件人邮箱")
    email_from: Optional[str] = Field(title="发件人邮箱")
    email_pwd: Optional[str] = Field(title="发件人邮箱密码")
    is_send: SendReportTypeEnum = Field(
        SendReportTypeEnum.on_fail.value, title="是否发送测试报告", description="not_send/always/on_fail")
    merge_notify: int = Field(0, title="多个环境时，是否合并通知（只通知一次）", description="默认不合并，0不合并、1合并")
    cron: str = required_str_field(title="cron表达式")
    name: str = required_str_field(title="任务名")
    skip_holiday: bool = Field(True, title="是否跳过节假日、调休日")
    conf: Optional[dict] = Field({}, title="运行配置", description="webUi存浏览器，appUi存运行服务器、手机、是否重置APP")
    is_async: int = Field(default=0, title="任务的运行机制", description="0：串行，1：并行，默认0")
    call_back: Optional[Union[list, dict]] = Field(title="回调给流水线")

    @field_validator("receive_type")
    def validate_receive_type(cls, value):
        return value.value

    @field_validator("is_send")
    def validate_is_send(cls, value, info: ValidationInfo):
        """ 发送报告类型 1.不发送、2.始终发送、3.仅用例不通过时发送 """
        if value in [SendReportTypeEnum.always.value, SendReportTypeEnum.on_fail.value]:
            receive_type = info.data["receive_type"]
            if receive_type in (ReceiveTypeEnum.ding_ding.value, ReceiveTypeEnum.we_chat.value):
                cls.validate_is_true(info.data["webhook_list"], '选择了要通过机器人发送报告，则webhook地址必填')
            elif receive_type == ReceiveTypeEnum.email.value:
                cls.validate_email(
                    info.data.get("email_server"), info.data.get("email_from"),
                    info.data.get("email_pwd"), info.data.get("email_to")
                )
        return value.value

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
    def validate_conf(cls, value, info: ValidationInfo):
        """ 校验任务运行配置 """
        cls.validate_is_true(value.get("browser"), '请选择运行浏览器')
        return value

    @field_validator("name")
    def validate_name(cls, value, info: ValidationInfo):
        """ 校验任务名不重复 """
        cls.validate_data_is_not_exist(
            f"当前项目中，任务名【{value}】已存在", Task, project_id=info.data["project_id"], name=value)
        return value


class EditTaskForm(AddTaskForm, GetTaskForm):
    """ 编辑任务 """

    @field_validator("id")
    def validate_id(cls, value):
        """ 校验id存在 """
        task = cls.validate_data_is_exist(f"任务id【{value}】不存在", Task, id=value)
        cls.validate_is_true(task.is_disable(), "任务的状态不为禁用中，请先禁用再修改")
        setattr(cls, "task", task)
        return value

    @field_validator("name")
    def validate_name(cls, value, info: ValidationInfo):
        """ 校验任务名不重复 """
        cls.validate_data_is_not_repeat(
            f"当前服务中，任务名【{value}】已存在",
            Task, info.data["id"], project_id=info.data["project_id"], name=value)
        return value


class RunTaskForm(GetTaskForm):
    """ 运行任务 """
    env_list: Optional[list] = Field(None, title="运行环境")
    is_async: int = Field(default=0, title="任务的运行机制", description="0：串行，1：并行，默认0")
    trigger_type: Optional[TriggerTypeEnum] = Field(
        TriggerTypeEnum.page, title="触发类型", description="pipeline/page/cron")  # pipeline 跑完过后会发送测试报告
    extend: Optional[Union[list, dict, str]] = Field(
        None, title="扩展字段", description="运维传过来的扩展字段，接收的什么就返回什么")
    browser: str = Field("chrome", title="浏览器")
