#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : SendEmail.py
# @Software: PyCharm
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header


class SendEmail:
    """ 发送测试报告到邮箱 """

    def __init__(self, email_server, username, password, to_list, file):
        self.email_server = email_server
        self.username = username
        self.password = password
        self.to_list = to_list
        self.file = file

    def send_email(self):
        """ 使用第三方SMTP服务发送邮件 """
        message = MIMEMultipart()
        body = MIMEText(_text=self.file, _subtype='html', _charset='utf-8')  # 邮件正文内容为报告附件body
        message.attach(body)
        message['From'] = Header("测试报告", 'utf-8')
        message['To'] = Header(''.join(self.to_list), 'utf-8')
        subject = '接口自动化测试报告邮件' if '>失败</th>' not in self.file else '接口自动化测试报告邮件，有执行失败的用例，请查看附件或登录平台查看'
        message['Subject'] = Header(subject, 'utf-8')

        # 添加附件
        att = MIMEText(self.file, "base64", "utf-8")
        att["Content-Type"] = "application/octet-stream"
        att["Content-Disposition"] = 'attachment; filename= "report.html"'
        message.attach(att)

        try:
            # 发送邮件
            print(f'{"=" * 30} 开始发送邮件，发件箱为 {self.username} {"=" * 30}')
            service = smtplib.SMTP_SSL(host=self.email_server, port=smtplib.SMTP_SSL_PORT)
            service.login(user=self.username, password=self.password)  # 登录
            service.sendmail(from_addr=self.username, to_addrs=self.to_list, msg=message.as_string())
            print(f'{"=" * 30} 邮件发送成功 {"=" * 30}')
            service.close()
        except Exception as error:
            print(f'发送邮件出错，错误信息为：\n {error}')
