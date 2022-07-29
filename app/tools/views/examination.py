# -*- coding: utf-8 -*-

import json
import os

from flask import current_app as app

from app.tools import tool

# 获取征信从业资格考试题目
with open(os.path.join(os.path.dirname(__file__), '../zhengXinTest.json'), encoding='utf8') as file:
    zheng_xin_test_data = json.load(file)


@tool.route('/examination', methods=['GET'])
def get_test_data_not_login_required():
    """ 征信考试 """
    return app.restful.success('获取成功', data=zheng_xin_test_data)
