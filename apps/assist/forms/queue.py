from typing import Optional, Union

from pydantic import Field, field_validator

from ...base_form import BaseForm, PaginationForm, required_str_field
from ..model_factory import QueueLink, QueueTopic, QueueMsgLog
from ...enums import QueueTypeEnum


class GetQueueLinkListForm(PaginationForm):
    host: Optional[str] = Field(None, title="队列链接地址")
    queue_type: Optional[str] = Field(None, title="队列类型")
    instance_id: Optional[str] = Field(None, title="rocket_mq 实例id")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.host:
            filter_list.append(QueueLink.host.like(f'%{self.host}%'))
        if self.queue_type:
            filter_list.append(QueueLink.queue_type == self.queue_type)
        if self.instance_id:
            filter_list.append(QueueLink.instance_id.like(f'%{self.instance_id}%'))
        return filter_list


class GetQueueLinkForm(BaseForm):
    id: int = Field(..., title="队列链接id")

    @field_validator("id")
    def validate_id(cls, value):
        queue = cls.validate_data_is_exist('数据不存在', QueueLink, id=value)
        setattr(cls, "queue_link", queue)
        return value


class CreatQueueLinkForm(BaseForm):
    queue_type: QueueTypeEnum = Field(title="队列类型", description="rocket_mq、rabbit_mq、redis，目前只支持mq")
    instance_id: Optional[str] = Field(None, title="rocket_mq 实例id")
    name: Optional[str] = Field(None, title="别名")
    host: str = required_str_field(title="地址")
    port: Optional[int] = Field(None, title="端口")
    account: Optional[str] = Field(None, title="rabbit_mq - 账号")
    password: Optional[str] = Field(None, title="rabbit_mq - 密码")
    access_id: Optional[str] = Field(None, title="rocket_mq - access_id")
    access_key: Optional[str] = Field(None, title="rocket_mq - access_key")
    desc: Optional[str] = Field(None, title="描述")


class EditQueueLinkForm(GetQueueLinkForm):
    """ 修改消息队列链接 """
    queue_type: QueueTypeEnum = Field(title="队列类型", description="rocket_mq、rabbit_mq、redis，目前只支持mq")
    instance_id: Optional[str] = Field(None, title="rocket_mq 实例id")
    name: Optional[str] = Field(None, title="别名")
    host: str = required_str_field(title="地址")
    desc: Optional[str] = Field(None, title="描述")


class GetQueueTopicListForm(PaginationForm):
    link_id: Optional[str] = Field(None, title="队列链接id")
    topic: Optional[str] = Field(None, title="topic名字")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.link_id:
            filter_list.append(QueueTopic.link_id == self.link_id)
        if self.topic:
            filter_list.append(QueueTopic.topic.like(f'%{self.topic}%'))
        return filter_list


class GetQueueTopicForm(BaseForm):
    id: int = Field(..., title="topic id")

    @field_validator("id")
    def validate_id(cls, value):
        topic = cls.validate_data_is_exist('数据不存在', QueueTopic, id=value)
        setattr(cls, "queue_topic", topic)
        return value


class DeleteQueueTopicForm(GetQueueTopicForm):
    """ 删除topic """


class CreatQueueTopicForm(BaseForm):
    """ 创建消息队列 """
    link_id: int = Field(..., title="所属消息队列链接id")
    topic: Optional[str] = Field(title="rocket_mq对应topic，rabbit_mq对应queue_name")
    desc: Optional[str] = Field(None, title="备注")


class EditQueueTopicForm(GetQueueTopicForm, CreatQueueTopicForm):
    """ 修改消息队列 """


class SendMessageForm(GetQueueTopicForm):
    """ 发送消息 """
    tag: Optional[str] = Field(None, title="tag")
    options: Optional[dict] = Field({}, title="用于指定参数，KEYS、或者其他自定义参数")
    message: Union[dict, list, str] = Field({}, title="消息内容")

    @field_validator("id")
    def validate_id(cls, value):
        topic = cls.validate_data_is_exist('数据不存在', QueueTopic, id=value)
        setattr(cls, "queue_topic", topic)

        query_set = QueueLink.db.session.query(
            QueueLink.id, QueueLink.queue_type, QueueLink.host, QueueLink.port, QueueLink.account,
            QueueLink.password, QueueLink.access_id, QueueLink.access_key, QueueLink.instance_id
        ).filter(QueueTopic.id == value, QueueLink.id == QueueTopic.link_id).one()
        cls.validate_is_true(query_set, "数据不存在")
        setattr(cls, "queue_link", {
            "link_id": query_set[0],
            "queue_type": query_set[1],
            "host": query_set[2],
            "port": query_set[3],
            "account": query_set[4],
            "password": query_set[5],
            "access_id": query_set[6],
            "access_key": query_set[7],
            "instance_id": query_set[8]
        })
        return value


class GetQueueMsgLogForm(PaginationForm):
    """ 获取消息队列的消息记录列表 """
    topic_id: int = Field(..., title="队列id")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = [QueueMsgLog.topic_id == self.topic_id]
        return filter_list
