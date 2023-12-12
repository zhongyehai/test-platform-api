# -*- coding: utf-8 -*-
import json
import os

from flask import current_app as app

from apps.tools.blueprint import tool


@tool.get("/examination")
def tool_get_examination():
    """ 获取征信从业资格考试题目 """
    with open(os.path.join(os.path.dirname(__file__), "../zheng_xin_test.json"), encoding="utf8") as file:
        zheng_xin_test_data = json.load(file)
    return app.restful.get_success(zheng_xin_test_data)
