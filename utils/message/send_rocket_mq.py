# -*- coding: utf-8 -*-
import json
import pika
import datetime


def send_rocket_mq(info, message):  # 消息生产者
    user_info = pika.PlainCredentials(info["account"], info["password"])
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=info["host"], port=info["port"], credentials=user_info))
    channel = connection.channel()
    channel.queue_declare(queue=info["queue_name"])  # 声明消息队列，消息将在这个队列传递，如不存在，则创建
    # 向队列插入数值 routing_key的队列名为tester，body 就是放入的消息内容，exchange指定消息在哪个队列传递，
    # 这里是空的exchange但仍然能够发送消息到队列中，因为使用的是定义的空字符串"" exchange（默认的exchange）
    channel.basic_publish(exchange='', routing_key=info["queue_name"], body=message)
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
    send_rocket_mq(mq_info, message)
