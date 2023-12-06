from typing import Optional

from pydantic import Field, field_validator, ValidationInfo

from ...base_form import BaseForm, PaginationForm, required_str_field
from ..model_factory import Queue, QueueMsgLog
from ...enums import QueueTypeEnum


class GetQueueLinkListForm(PaginationForm):
    """ 获取消息队列链接列表 """
    host: Optional[str] = Field(None, title="队列链接地址")
    queue_type: Optional[str] = Field(None, title="队列类型")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = [Queue.link_id.is_(None)]
        if self.host:
            filter_list.append(Queue.host.like(f'%{self.host}%'))
        if self.queue_type:
            filter_list.append(Queue.queue_type == self.queue_type)
        return filter_list


class GetQueueForm(BaseForm):
    """ 获取消息队列 """
    id: int = Field(..., title="队列id")

    @field_validator("id")
    def validate_id(cls, value):
        """ 校验自定义脚本文件需存在 """
        queue = cls.validate_data_is_exist('数据不存在', Queue, id=value)
        setattr(cls, "queue", queue)
        return value


class DeleteQueueForm(GetQueueForm):
    """ 删除消息队列 """


class CreatQueueLinkForm(BaseForm):
    """ 创建息队列链接 """
    queue_type: QueueTypeEnum = Field(title="队列类型", description="rocket_mq、redis，目前只支持mq")
    host: str = required_str_field(title="地址")
    port: int = Field(5672, title="端口")
    account: str = required_str_field(title="账号")
    password: str = required_str_field(title="密码")
    desc: Optional[str] = Field(title="描述")


class EditQueueLinkForm(GetQueueForm, CreatQueueLinkForm):
    """ 修改消息队列链接 """


class SendMessageForm(GetQueueForm):
    """ 发送消息 """
    message: str = required_str_field(title="消息内容")

    @field_validator("id")
    def validate_id(cls, value):
        """ 校验自定义脚本文件需存在 """
        queue = cls.validate_data_is_exist('数据不存在', Queue, id=value)
        queue_link = cls.validate_data_is_exist('数据不存在', Queue, id=queue.link_id)
        queue_link_dict = queue_link.to_dict()
        queue_link_dict["queue_name"] = queue.queue_name
        setattr(cls, "queue_link", queue_link_dict)
        return value


class GetQueueListForm(PaginationForm):
    """ 获取具体链接下的消息队列列表 """
    link_id: int = Field(..., title="队列链接id")
    queue_name: Optional[str] = Field(None, title="队列名")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = [Queue.link_id == self.link_id]
        if self.queue_name:
            filter_list.append(Queue.queue_name.like(f'%{self.queue_name}%'))
        return filter_list


class CreatQueueForm(BaseForm):
    """ 创建消息队列 """
    link_id: int = Field(..., title="所属消息队列链接id")
    queue_name: Optional[str] = Field(title="队列名")
    desc: Optional[str] = Field(title="描述")


class EditQueueForm(GetQueueForm, CreatQueueForm):
    """ 修改消息队列 """


class GetQueueMsgLogForm(PaginationForm):
    """ 获取消息队列的消息记录列表 """
    queue_id: int = Field(..., title="队列id")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = [QueueMsgLog.queue_id == self.queue_id]
        return filter_list
