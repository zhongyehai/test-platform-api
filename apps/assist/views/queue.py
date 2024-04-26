# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import assist
from ..model_factory import QueueLink, QueueTopic, QueueMsgLog
from ...base_form import ChangeSortForm
from ..forms.queue import GetQueueLinkListForm, GetQueueLinkForm, CreatQueueLinkForm, EditQueueLinkForm, \
    GetQueueTopicListForm, GetQueueTopicForm, CreatQueueTopicForm, EditQueueTopicForm, DeleteQueueTopicForm, \
    SendMessageForm, GetQueueMsgLogForm

from utils.message.send_mq import send_rabbit_mq, send_rocket_mq
from ...enums import QueueTypeEnum


@assist.login_get("/queue-link/list")
def assist_get_queue_link_list():
    """ 消息队列链接列表 """
    form = GetQueueLinkListForm()
    get_filed = [QueueLink.id, QueueLink.queue_type, QueueLink.host, QueueLink.port, QueueLink.desc,
                 QueueLink.instance_id, QueueLink.create_user]
    return app.restful.get_success(QueueLink.make_pagination(form, get_filed=get_filed))


@assist.login_put("/queue-link/sort")
def assist_change_queue_link_sort():
    """ 更新消息队列排序 """
    form = ChangeSortForm()
    QueueLink.change_sort(**form.model_dump())
    return app.restful.change_success()


@assist.login_get("/queue-link")
def assist_get_queue_link():
    """ 获取消息队列链接 """
    form = GetQueueLinkForm()
    queue_link_dict = form.queue_link.to_dict()
    queue_link_dict.pop('account')
    queue_link_dict.pop('password')
    queue_link_dict.pop('access_id')
    queue_link_dict.pop('access_key')
    return app.restful.get_success(queue_link_dict)


@assist.login_post("/queue-link")
def assist_add_queue_link():
    """ 新增消息队列链接 """
    form = CreatQueueLinkForm()
    QueueLink.model_create(form.model_dump())
    return app.restful.add_success()


@assist.login_put("/queue-link")
def assist_change_queue_link():
    """ 修改消息队列链接 """
    form = EditQueueLinkForm()
    form.queue_link.model_update(form.model_dump())
    return app.restful.change_success()


@assist.login_get("/queue-topic/list")
def assist_get_queue_topic_list():
    """ 消息队列列表 """
    form = GetQueueTopicListForm()
    get_filed = [QueueTopic.id, QueueTopic.link_id, QueueTopic.topic, QueueTopic.desc, QueueTopic.create_user]
    return app.restful.get_success(QueueTopic.make_pagination(form, get_filed=get_filed))


@assist.login_put("/queue-topic/sort")
def assist_change_queue_topic_sort():
    """ 更新消息队列排序 """
    form = ChangeSortForm()
    QueueTopic.change_sort(**form.model_dump())
    return app.restful.change_success()


@assist.login_post("/queue-topic/copy")
def assist_copy_queue_topic():
    """ 复制消息队列 """
    form = GetQueueTopicForm()
    form.queue_topic.copy()
    return app.restful.copy_success()


@assist.login_get("/queue-topic")
def assist_get_queue_topic():
    """ 获取消息队列 """
    form = GetQueueTopicForm()
    return app.restful.get_success(form.queue_topic.to_dict())


@assist.login_post("/queue-topic")
def assist_add_queue_topic():
    """ 新增消息队列 """
    form = CreatQueueTopicForm()
    QueueTopic.model_create(form.model_dump())
    return app.restful.add_success()


@assist.login_put("/queue-topic")
def assist_change_queue_topic():
    """ 修改消息队列 """
    form = EditQueueTopicForm()
    form.queue_topic.model_update(form.model_dump())
    return app.restful.change_success()


@assist.login_delete("/queue-topic")
def assist_delete_queue_topic():
    """ 删除消息队列 """
    form = DeleteQueueTopicForm()
    form.queue_topic.delete()
    return app.restful.delete_success()


@assist.login_post("/queue-topic/message")
def assist_send_message_to_queue():
    """ 发送消息队列 """
    form = SendMessageForm()
    match form.queue_link["queue_type"]:
        case QueueTypeEnum.rabbit_mq:
            send_res = send_rabbit_mq(
                form.queue_link["host"],
                form.queue_link["port"],
                form.queue_link["account"],
                form.queue_link["password"],
                form.queue_link["topic"],
                form.message
            )
        case QueueTypeEnum.rocket_mq:
            send_res = send_rocket_mq(
                form.queue_link["host"],
                form.queue_link["access_id"],
                form.queue_link["access_key"],
                form.queue_topic.topic,
                form.queue_link["instance_id"],
                form.message,
                form.tag,
                form.options
            )
        case _:
            return app.restful.fail("不支持当前队列")
    QueueMsgLog.model_create({
        "link_id": form.queue_link["link_id"],
        "topic_id": form.id,
        "tag": form.tag,
        "options": form.options,
        "message": form.message,
        "status": send_res["status"],
        "response": send_res["res"]
    })
    return app.restful.success('消息发送完成')


@assist.login_get("/queue-topic/log")
def assist_get_queue_log_list():
    """ 消息发送记录 """
    form = GetQueueMsgLogForm()
    get_filed = [
        QueueMsgLog.id, QueueMsgLog.topic_id, QueueMsgLog.tag, QueueMsgLog.options, QueueMsgLog.message, QueueMsgLog.status,
        QueueMsgLog.response, QueueMsgLog.create_user, QueueMsgLog.create_time
    ]
    return app.restful.get_success(QueueMsgLog.make_pagination(form, get_filed=get_filed))
