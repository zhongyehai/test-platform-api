# -*- coding: utf-8 -*-
from datetime import datetime
from threading import Thread

import requests

from app.config.model_factory import Config
from app.assist.model_factory import CallBack
from app.enums import SendReportTypeEnum, ReceiveTypeEnum
from .send_email import SendEmail
from .template import diff_api_msg, run_time_error_msg, call_back_webhook_msg, render_html_report, \
    get_inspection_msg, get_business_stage_count_msg
from ..logs.log import logger
from config import _default_web_hook


def send_msg(addr, msg):
    """ 发送消息 """
    logger.info(f'发送消息，文本：{msg}')
    try:
        logger.info(f'发送消息，结果：{requests.post(addr, json=msg, verify=False).json()}')
    except Exception as error:
        logger.info(f'向机器人发送测试报告失败，错误信息：\n{error}')


def send_server_status(server_name, app_title=None, action_type="启动"):
    """ 服务启动/关闭成功 """
    msg = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"服务{action_type}通知",
            "text": f'### 服务{action_type}通知 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} \n> '
                    f'#### 服务<font color=#FF0000>【{server_name}】【{app_title}】</font>{action_type}完成 \n> '
        }
    }
    send_msg(_default_web_hook, msg)


def send_system_error(title, content):
    """ 系统报错 """
    msg = {
        "msgtype": "text",
        "text": {
            "content": f"""{title}:\n{content}"""
        }
    }
    send_msg(_default_web_hook, msg)


def send_inspection_by_msg(receive_type, content, kwargs):
    """ 发送巡检消息 """
    msg = get_inspection_msg(receive_type, content, kwargs)
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
    if is_send == SendReportTypeEnum.ALWAYS.value or (
            is_send == SendReportTypeEnum.ON_FAIL.value and content["result"] != "success"):
        if receive_type == ReceiveTypeEnum.EMAIL:
            send_inspection_by_email(content, kwargs)
        else:
            send_inspection_by_msg(receive_type, content, kwargs)


def async_send_report(**kwargs):
    """ 多线程发送测试报告 """
    Thread(target=send_report, kwargs=kwargs).start()


def call_back_for_pipeline(task_id, call_back_info: list, extend: dict, status):
    """ 把测试结果回调给流水线 """
    logger.info("开始执行回调")
    for call_back in call_back_info:
        logger.info(f'开始回调{call_back.get("url")}')
        call_back.get('json', {})["status"] = status
        call_back.get('json', {})["taskId"] = task_id
        call_back.get('json', {})["extend"] = extend

        call_back_obj = CallBack.model_create_and_get({
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
            logger.info(f'回调{call_back.get("url")}结束: \n{call_back_res}')
            msg = call_back_webhook_msg(call_back.get("json", {}))
            send_msg(Config.get_call_back_msg_addr(), msg)
        except Exception as error:
            logger.info(f'回调{call_back.get("url")}失败')
            call_back_obj.fail()
            send_system_error(title="回调报错通知", content=f'{error}')  # 发送通知
    logger.info("回调执行结束")


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
    logger.info("开始发送错误信息")
    Thread(target=send_run_time_error_message, kwargs=kwargs).start()
    logger.info("错误信息发送完毕")


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
