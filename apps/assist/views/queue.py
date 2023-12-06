# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import assist
from ..model_factory import Queue, QueueMsgLog
from ...base_form import ChangeSortForm
from ..forms.queue import GetQueueForm, DeleteQueueForm, GetQueueLinkListForm, GetQueueListForm, CreatQueueLinkForm, \
    EditQueueLinkForm, CreatQueueForm, EditQueueForm, SendMessageForm, GetQueueMsgLogForm
from utils.message.send_rocket_mq import send_rocket_mq
from ...enums import QueueTypeEnum


@assist.login_get("/queue-link/list")
def assist_get_queue_link_list():
    """ 消息队列链接列表 """
    form = GetQueueLinkListForm()
    get_filed = [Queue.id, Queue.queue_type, Queue.host, Queue.port, Queue.desc, Queue.create_user]
    return app.restful.get_success(Queue.make_pagination(form, get_filed=get_filed))


@assist.login_post("/queue-link")
def assist_add_queue_link():
    """ 新增消息队列链接 """
    form = CreatQueueLinkForm()
    Queue.model_create(form.model_dump())
    return app.restful.add_success()


@assist.login_put("/queue-link")
def assist_change_queue_link():
    """ 修改消息队列链接 """
    form = EditQueueLinkForm()
    form.queue.model_update(form.model_dump())
    return app.restful.change_success()


@assist.login_get("/queue/list")
def assist_get_queue_list():
    """ 消息队列列表 """
    form = GetQueueListForm()
    get_filed = [Queue.id, Queue.link_id, Queue.queue_name, Queue.desc, Queue.create_user]
    return app.restful.get_success(Queue.make_pagination(form, get_filed=get_filed))


@assist.login_post("/queue")
def assist_add_queue():
    """ 新增消息队列 """
    form = CreatQueueForm()
    Queue.model_create(form.model_dump())
    return app.restful.add_success()


@assist.login_put("/queue")
def assist_change_queue():
    """ 修改消息队列 """
    form = EditQueueForm()
    form.queue.model_update(form.model_dump())
    return app.restful.change_success()


@assist.login_post("/queue/message")
def assist_send_message_to_queue():
    """ 发送消息队列 """
    form = SendMessageForm()
    if form.queue_link["queue_type"] == QueueTypeEnum.rocket_mq:
        send_rocket_mq(form.queue_link, form.message)
    QueueMsgLog.model_create({"queue_id": form.id, "message": form.message})
    return app.restful.success('消息发送完成')


@assist.login_get("/queue")
def assist_get_queue():
    """ 获取消息队列 """
    form = GetQueueForm()
    return app.restful.get_success(form.queue.to_dict())


@assist.login_delete("/queue")
def assist_delete_queue():
    """ 删除消息队列 """
    form = DeleteQueueForm()
    form.queue.delete()
    return app.restful.delete_success()


@assist.login_put("/queue/sort")
def assist_change_queue_sort():
    """ 更新消息队列排序 """
    form = ChangeSortForm()
    Queue.change_sort(**form.model_dump())
    return app.restful.change_success()


@assist.login_post("/queue/copy")
def assist_copy_link():
    """ 复制消息队列 """
    form = GetQueueForm()
    form.queue.copy()
    return app.restful.copy_success()


@assist.login_get("/queue-log/list")
def assist_get_queue_log_list():
    """ 消息发送记录 """
    form = GetQueueMsgLogForm()
    get_filed = [
        QueueMsgLog.id, QueueMsgLog.queue_id, QueueMsgLog.message, QueueMsgLog.create_user, QueueMsgLog.create_time
    ]
    return app.restful.get_success(QueueMsgLog.make_pagination(form, get_filed=get_filed))
