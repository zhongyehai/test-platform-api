# -*- coding: utf-8 -*-
import pika
import datetime

from .mq_http_sdk.mq_producer import *
from .mq_http_sdk.mq_client import *


def send_rocket_mq(host, access_id, access_key, topic, instance_id, message_body, message_tag, options: dict):
    mq_client = MQClient(host, access_id, access_key)  # 初始化client。
    producer = mq_client.get_producer(instance_id, topic)
    try:
        body = message_body if isinstance(message_body, str) else json.dumps(message_body)
        message = TopicMessage(body, message_tag)
        for key, value in options.items():  # 自定义的属性
            if value:
                message.set_message_key(value) if key.upper() == "KEYS" else message.put_property(key, value)
        re_msg = producer.publish_message(message)
        return {"status": "success", "res": f"MessageID: {re_msg.message_id}, BodyMD5: {re_msg.message_body_md5}"}
    except MQExceptionBase as error:
        return {"status": "fail", "res": error}


def send_rabbit_mq(host, port, account, password, topic, message):  # 消息生产者
    user_info = pika.PlainCredentials(account, password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=host, port=port, credentials=user_info))
    channel = connection.channel()
    channel.queue_declare(queue=topic)  # 声明消息队列，消息将在这个队列传递，如不存在，则创建
    # 向队列插入数值 routing_key的队列名为tester，body 就是放入的消息内容，exchange指定消息在哪个队列传递，
    # 这里是空的exchange但仍然能够发送消息到队列中，因为使用的是定义的空字符串"" exchange（默认的exchange）
    channel.basic_publish(exchange='', routing_key=topic, body=message)
    connection.close()  # 关闭连接


if __name__ == "__main__":
    mq_info = {
        "host": '127.0.0.1',
        "port": 5672,
        "account": "guest",
        "password": "guest",
        "queue_name": "test1",
    }
    message = json.dumps({"create_time": str(datetime.datetime.now())})
    print(message)
    send_rabbit_mq(**mq_info, message=message)
