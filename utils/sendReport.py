# -*- coding: utf-8 -*-

from datetime import datetime
from threading import Thread

import requests

from utils.sendEmail import SendEmail
from utils.report.report import render_html_report
from app.config.models.config import Config
from config.config import conf


# def by_we_chat(content, webhook, report_id):
def by_we_chat(content, kwargs):
    """ 通过企业微信器人发送测试报告 """
    msg = {
        "msgtype": "markdown",
        "markdown": {
            "content": f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
                       f'任务名：{content["stat"]["testcases"]["project"]} \n'
                       f'>执行用例:<font color="comment"> {content["stat"]["testcases"]["total"]} </font>条\n'
                       f'>成功:<font color="info"> {content["stat"]["testcases"]["success"]} </font>条\n'
                       f'>失败:<font color="warning"> {content["stat"]["testcases"]["fail"]} </font>条\n'
                       f'详情请登录[测试平台]({kwargs["report_addr"] + str(kwargs["report_id"])})查看'
        }
    }
    print(msg)
    try:
        print(f'测试结果通过企业微信机器人发送：{requests.post(kwargs["we_chat"], json=msg, verify=False).json()}')
    except Exception as error:
        print(f'向企业微信发送测试报告失败，错误信息：\n{error}')


# def by_ding_ding(content, webhook, report_id):
def by_ding_ding(content, kwargs):
    """ 通过钉钉机器人发送测试报告 """
    msg = {
        "msgtype": "markdown",
        "markdown": {
            "title": "测试报告",
            "text": f'## 测试报告 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} \n> '
                    f'### 任务名：{content["stat"]["testcases"]["project"]} \n> '
                    f'#### 执行用例:<font color=#3498DB> {content["stat"]["testcases"]["total"]} </font>条 \n> '
                    f'#### 成功:<font color=#27AE60> {content["stat"]["testcases"]["success"]} </font>条 \n> '
                    f'#### 失败:<font color=#E74C3C> {content["stat"]["testcases"]["fail"]} </font>条 \n> '
                    f'#### 详情请登录[测试平台]({kwargs["report_addr"] + str(kwargs["report_id"])})查看\n'
        }
    }
    print(msg)
    try:
        print(f'测试结果通过钉钉机器人发送：{requests.post(kwargs["ding_ding"], json=msg, verify=False).json()}')
    except Exception as error:
        print(f'向钉钉机器人发送测试报告失败，错误信息：\n{error}')


def by_email(content, kwargs):
    """ 通过邮件发送测试报告 """
    SendEmail(
        kwargs.get('email_server'),
        kwargs.get('email_from').strip(),
        kwargs.get('email_pwd'),
        [email.strip() for email in kwargs.get('email_to').split(';') if email],
        render_html_report(content)
    ).send_email()


def send_report(**kwargs):
    """ 封装发送测试报告提供给多线程使用 """
    is_send, send_type, content = kwargs.get('is_send'), kwargs.get('send_type'), kwargs.get('content')
    if is_send == '2' or (is_send == '3' and content['success'] is False):
        if send_type == 'we_chat':
            by_we_chat(content, kwargs)
        elif send_type == 'ding_ding':
            by_ding_ding(content, kwargs)
        elif send_type == 'email':
            by_email(content, kwargs)
        elif send_type == 'all':
            by_we_chat(content, kwargs)
            by_ding_ding(content, kwargs)
            by_email(content, kwargs)


def async_send_report(**kwargs):
    """ 多线程发送测试报告 """
    print('开始多线程发送测试报告')
    Thread(target=send_report, kwargs=kwargs).start()
    print('多线程发送测试报告完毕')


def call_back_for_pipeline(call_back_info: list, status):
    """ 把测试结果回调给流水线 """
    print('开始执行回调')
    for call_back in call_back_info:
        try:
            print(f'开始回调{call_back.get("url")}')
            for key, value in call_back.get('json', {}).items():
                if value == '$status':
                    call_back.get('json', {})[key] = status
            call_back_res = requests.request(**call_back).json()
            print(f'回调{call_back.get("url")}结束: \n{call_back_res}')
        except Exception as error:
            print(f'回调{call_back.get("url")}失败')
            # 发送即时通讯通知
            try:
                requests.post(
                    url=conf['error_push']['url'],
                    json={
                        'key': conf['error_push']['key'],
                        'head': f'回调{call_back.get("url")}报错了',
                        'body': f'{error}'
                    }
                )
            except Exception as error:
                print(f'发送回调错误消息失败')
    print('回调执行结束')


def send_diff_api_message(content, report_id, addr):
    """ 发送接口对比报告 """
    msg = {
        "msgtype": "markdown",
        "markdown": {
            "title": "接口监控",
            "text": f'## 接口监控 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} \n> '
                    f'### 任务名：{content["title"]} \n> '
                    f'#### 对比服务:<font color=#27AE60> {content["project"]["totle"]} </font>个 \n> '
                    f'##### 新增服务:<font color=#27AE60> {content["project"]["add"]} </font>个 \n> '
                    f'##### 修改服务:<font color=#3498DB> {content["project"]["modify"]} </font>个 \n> '
                    f'##### 删除服务:<font color=#E74C3C> {content["project"]["remove"]} </font>个 \n> '
                    f'##### 乱码:<font color=#E74C3C> {content["project"]["errorCode"]} </font>个 \n> '
                    f'##### \n> '
                    f'#### 对比模块:<font color=#27AE60> {content["module"]["totle"]} </font>个 \n> '
                    f'##### 新增模块:<font color=#27AE60> {content["module"]["add"]} </font>个 \n> '
                    f'##### 修改模块:<font color=#3498DB> {content["module"]["modify"]} </font>个 \n> '
                    f'##### 删除模块:<font color=#E74C3C> {content["module"]["remove"]} </font>个 \n> '
                    f'##### 乱码:<font color=#E74C3C> {content["module"]["errorCode"]} </font>个 \n> '
                    f'##### \n> '
                    f'#### 对比接口:<font color=#27AE60> {content["api"]["totle"]} </font>个 \n> '
                    f'##### 新增接口:<font color=#27AE60> {content["api"]["add"]} </font>个 \n> '
                    f'##### 修改接口:<font color=#3498DB> {content["api"]["modify"]} </font>个 \n> '
                    f'##### 删除接口:<font color=#E74C3C> {content["api"]["remove"]} </font>个 \n> '
                    f'##### 乱码:<font color=#E74C3C> {content["api"]["errorCode"]} </font>个 \n> '
                    f'##### \n> '
                    f'#### 请登录[测试平台]({Config.get_diff_api_addr()}{str(report_id)})查看详情，并确认是否更新\n'
            # f'#### 请登录[测试平台]({conf["diff_addr"]}{str(report_id)})查看详情，并确认是否更新\n'
        }
    }
    try:
        print(f'测试结果通过钉钉机器人发送：{requests.post(addr, json=msg, verify=False).json()}')
    except Exception as error:
        print(f'向钉钉机器人发送测试报告失败，错误信息：\n{error}')


def send_run_time_error_message(content, addr):
    """ 执行自定义函数时发生了异常的报告 """
    msg = {
        "msgtype": "markdown",
        "markdown": {
            "title": content.get("title"),
            # "text": content.get("detail") + f'#### 详情请登录[测试平台]({conf["error_addr"]})查看\n'
            "text": content.get("detail") + f'#### 详情请登录[测试平台]({Config.get_func_error_addr()})查看\n'
        }
    }
    print(msg)
    try:
        print(f'发送错误通知：{requests.post(addr, json=msg, verify=False).json()}')
    except Exception as error:
        print(f'向钉钉机器人发送错误通知失败，错误信息：\n{error}')


def async_send_run_time_error_message(**kwargs):
    """ 多线程发送错误信息 """
    print('开始多线程发送错误信息')
    Thread(target=send_run_time_error_message, kwargs=kwargs).start()
    print('多线程发送错误信息完毕')


if __name__ == '__main__':
    pass
