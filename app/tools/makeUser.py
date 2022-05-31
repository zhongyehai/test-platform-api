# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/10/19 14:51
# @Author : ZhongYeHai
# @Site :
# @File : makeUser.py
# @Software: PyCharm
import json

from faker import Faker
from flask import request

from app.tools import tool
from app.utils import restful, makeUserTools
from app.config.models import Config

fake = Faker('zh_CN')


@tool.route('/makeUserMapping', methods=['GET'])
def get_make_user_info_mapping():
    """ 获取生成用户信息可选项映射关系 """
    return restful.success('获取成功', data=Config.get_first(name='make_user_info_mapping').value)


@tool.route('/makeUser', methods=['GET'])
def make_user_info():
    """ 生成用户信息 """
    args = request.args.to_dict()
    count, options, all_data = int(args.get('count')), json.loads(args.get('options')), []
    for option in options:
        temp_data = []
        if hasattr(fake, option) or option == 'credit_code':
            i = 0
            while True:
                if i >= count:
                    break
                data = makeUserTools.get_credit_code() if option == 'credit_code' else getattr(fake, option)()
                if data not in temp_data:
                    temp_data.append(data)
                    i += 1
        all_data.append(temp_data)
    return restful.success('获取成功', data=[dict(zip(options, data)) for data in zip(*all_data)])
