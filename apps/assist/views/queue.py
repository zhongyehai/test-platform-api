# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import assist
from ..model_factory import QueueInstance, QueueTopic, QueueMsgLog
from ...base_form import ChangeSortForm
from ..forms.queue import GetQueueInstanceListForm, GetQueueInstanceForm, CreatQueueInstanceForm, EditQueueInstanceForm, \
    GetQueueTopicListForm, GetQueueTopicForm, CreatQueueTopicForm, EditQueueTopicForm, DeleteQueueTopicForm, \
    SendMessageForm, GetQueueMsgLogForm

from utils.message.send_mq import send_rabbit_mq, send_rocket_mq, send_active_mq
from ...enums import QueueTypeEnum


@assist.login_get("/queue-instance/list")
def assist_get_queue_instance_list():
    """ 消息队列实例列表 """
    form = GetQueueInstanceListForm()
    get_filed = [QueueInstance.id, QueueInstance.queue_type, QueueInstance.host, QueueInstance.port, QueueInstance.desc,
                 QueueInstance.instance_id, QueueInstance.create_user]
    return app.restful.get_success(QueueInstance.make_pagination(form, get_filed=get_filed))


@assist.login_put("/queue-instance/sort")
def assist_change_queue_instance_sort():
    """ 更新消息队列排序 """
    form = ChangeSortForm()
    QueueInstance.change_sort(**form.model_dump())
    return app.restful.change_success()


@assist.login_get("/queue-instance")
def assist_get_queue_instance():
    """ 获取消息队列实例 """
    form = GetQueueInstanceForm()
    queue_instance_dict = form.queue_instance.to_dict()
    queue_instance_dict.pop('account')
    queue_instance_dict.pop('password')
    queue_instance_dict.pop('access_id')
    queue_instance_dict.pop('access_key')
    return app.restful.get_success(queue_instance_dict)


@assist.login_post("/queue-instance")
def assist_add_queue_instance():
    """ 新增消息队列实例 """
    form = CreatQueueInstanceForm()
    QueueInstance.model_create(form.model_dump())
    return app.restful.add_success()


@assist.login_put("/queue-instance")
def assist_change_queue_instance():
    """ 修改消息队列实例 """
    form = EditQueueInstanceForm()
    form.queue_instance.model_update(form.model_dump())
    return app.restful.change_success()


@assist.login_get("/queue-topic/list")
def assist_get_queue_topic_list():
    """ 消息队列列表 """
    form = GetQueueTopicListForm()
    get_filed = [QueueTopic.id, QueueTopic.instance_id, QueueTopic.topic, QueueTopic.desc, QueueTopic.create_user]
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
    match form.queue_instance["queue_type"]:
        case QueueTypeEnum.rabbit_mq:
            send_res = send_rabbit_mq(
                form.queue_instance["host"],
                form.queue_instance["port"],
                form.queue_instance["account"],
                form.queue_instance["password"],
                form.queue_topic.topic,
                form.message
            )
        case QueueTypeEnum.rocket_mq:
            send_res = send_rocket_mq(
                form.queue_instance["host"],
                form.queue_instance["access_id"],
                form.queue_instance["access_key"],
                form.queue_topic.topic,
                form.queue_instance["instance_id"],
                form.message,
                form.tag,
                form.options
            )
        case QueueTypeEnum.active_mq:
            send_res = send_active_mq(
                form.queue_instance["host"],
                form.queue_instance["port"],
                form.queue_instance["account"],
                form.queue_instance["password"],
                form.queue_instance["instance_id"],
                form.queue_topic.topic,
                form.message
            )
        case _:
            return app.restful.fail("不支持当前队列")
    QueueMsgLog.model_create({
        "instance_id": form.queue_instance["id"],
        "topic_id": form.id,
        "tag": form.tag,
        "options": form.options,
        "message": form.message,
        "message_type": form.message_type,
        "status": send_res["status"],
        "response": send_res["res"]
    })
    return app.restful.success('消息发送完成')


@assist.login_get("/queue-topic/log")
def assist_get_queue_log_list():
    """ 消息发送记录 """
    form = GetQueueMsgLogForm()
    get_filed = [
        QueueMsgLog.id, QueueMsgLog.topic_id, QueueMsgLog.tag, QueueMsgLog.options, QueueMsgLog.message_type,
        QueueMsgLog.message, QueueMsgLog.status, QueueMsgLog.response, QueueMsgLog.create_user, QueueMsgLog.create_time
    ]
    return app.restful.get_success(QueueMsgLog.make_pagination(form, get_filed=get_filed))
