# -*- coding: utf-8 -*-
from threading import Thread

import requests

from utils.message.sendEmail import SendEmail
from utils.message.template import diff_api_msg, run_time_error_msg, call_back_webhook_msg, render_html_report, \
    get_inspection_msg, get_business_stage_count_msg
from app.baseModel import Config
from app.assist.models.callBack import CallBack
from config import error_push


def send_msg(addr, msg):
    """ 发送消息 """
    print(msg)
    try:
        print(f'发送消息：{requests.post(addr, json=msg, verify=False).json()}')
    except Exception as error:
        print(f'向机器人发送测试报告失败，错误信息：\n{error}')


def send_inspection_by_msg(receive_type, content, kwargs):
    """ 发送巡检消息 """
    msg = get_inspection_msg(receive_type, content, kwargs)
    print(msg)
    for webhook in kwargs["webhook_list"]:
        if webhook:
            send_msg(webhook, msg)


def send_inspection_by_email(content, kwargs):
    """ 通过邮件发送测试报告 """
    SendEmail(
        kwargs.get("email_server"),
        kwargs.get("email_from").strip(),
        kwargs.get("email_pwd"),
        [email.strip() for email in kwargs.get("email_to") if email],
        render_html_report(content, kwargs)
    ).send_email()


def send_report(**kwargs):
    """ 封装发送测试报告提供给多线程使用 """
    is_send, receive_type, content = kwargs.get("is_send"), kwargs.get("receive_type"), kwargs.get("content")
    if is_send == "2" or (is_send == "3" and content["success"] is False):
        if receive_type == "email":
            send_inspection_by_email(content, kwargs)
        else:
            send_inspection_by_msg(receive_type, content, kwargs)


def async_send_report(**kwargs):
    """ 多线程发送测试报告 """
    print("开始多线程发送测试报告")
    Thread(target=send_report, kwargs=kwargs).start()
    print("多线程发送测试报告完毕")


def call_back_for_pipeline(task_id, call_back_info: list, extend: dict, status):
    """ 把测试结果回调给流水线 """
    print("开始执行回调")
    for call_back in call_back_info:
        print(f'开始回调{call_back.get("url")}')
        call_back.get('json', {})["status"] = status
        call_back.get('json', {})["taskId"] = task_id
        call_back.get('json', {})["extend"] = extend

        call_back_obj = CallBack().create({
            "ip": None,
            "url": call_back.get("url", None),
            "method": call_back.get("method", None),
            "headers": call_back.get("headers", {}),
            "params": call_back.get("args", {}),
            "data_form": call_back.get("form", {}),
            "data_json": call_back.get("json", {}),
        })

        try:
            call_back_res = requests.request(**call_back).text
            call_back_obj.success(call_back_res)
            print(f'回调{call_back.get("url")}结束: \n{call_back_res}')
            msg = call_back_webhook_msg(call_back.get("json", {}))
            send_msg(Config.get_call_back_msg_addr(), msg)
        except Exception as error:
            print(f'回调{call_back.get("url")}失败')
            call_back_obj.fail()
            # 发送即时通讯通知
            try:
                requests.post(
                    url=error_push.get("url"),
                    json={
                        "key": error_push.get("key"),
                        "head": f'回调{call_back.get("url")}报错了',
                        "body": f'{error}'
                    }
                )
            except Exception as error:
                print("发送回调错误消息失败")
    print("回调执行结束")


def send_diff_api_message(content, report_id, addr):
    """ 发送接口对比报告 """
    msg = diff_api_msg(content, Config.get_report_host(), Config.get_diff_api_addr(), report_id)
    send_msg(addr, msg)


def send_run_time_error_message(content, addr):
    """ 执行自定义函数时发生了异常的报告 """
    msg = run_time_error_msg(content, Config.get_report_host(), Config.get_func_error_addr())
    send_msg(addr, msg)


def async_send_run_time_error_message(**kwargs):
    """ 多线程发送错误信息 """
    print("开始多线程发送错误信息")
    Thread(target=send_run_time_error_message, kwargs=kwargs).start()
    print("多线程发送错误信息完毕")


def send_run_func_error_message(content):
    """ 运行自定义函数错误通知 """
    async_send_run_time_error_message(
        content=content,
        addr=f'{Config.get_report_host()}{Config.get_run_time_error_message_send_addr()}'
    )


def send_business_stage_count(content):
    """ 发送阶段统计报告 """
    # if content["total"]:
    msg = get_business_stage_count_msg(content)
    for webhook in content["webhookList"]:
        send_msg(webhook, msg)


if __name__ == "__main__":
    pass
