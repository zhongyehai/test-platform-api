# -*- coding: utf-8 -*-

import json
import os

from app.tools import tool
from utils import restful

# 获取征信从业资格考试题目
with open(os.path.join(os.path.dirname(__file__), '../zhengXinTest.json'), encoding='utf8') as file:
    zheng_xin_test_data = json.load(file)


@tool.route('/examination', methods=['GET'])
def get_test_data():
    """ 征信考试 """
    return restful.success('获取成功', data=zheng_xin_test_data)
