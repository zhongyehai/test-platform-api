# -*- coding: utf-8 -*-

import json
import os

from flask import current_app as app

from app.baseView import NotLoginView
from app.tools.blueprint import tool


class GetTestDataView(NotLoginView):

    def get(self):
        """ 获取征信从业资格考试题目 """
        with open(os.path.join(os.path.dirname(__file__), '../zhengXinTest.json'), encoding='utf8') as file:
            zheng_xin_test_data = json.load(file)
        return app.restful.success('获取成功', data=zheng_xin_test_data)


tool.add_url_rule('/examination', view_func=GetTestDataView.as_view('GetTestDataView'))
