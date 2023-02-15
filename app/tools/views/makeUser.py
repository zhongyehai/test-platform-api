# -*- coding: utf-8 -*-
import json

from faker import Faker
from flask import request, current_app as app

from app.baseView import NotLoginView
from app.tools.blueprint import tool
from utils.makeData import makeUserTools


class MakeUserInfoView(NotLoginView):

    def get(self):
        """ 生成用户信息 """
        all_data, args = [], request.args.to_dict()
        language, count, options = args.get("language"), int(args.get("count")), json.loads(args.get("options"))
        fake = Faker(language)
        for option in options:
            temp_data = []
            if hasattr(fake, option) or option == "credit_code":
                i = 0
                while True:
                    if i >= count:
                        break
                    data = makeUserTools.get_credit_code() if option == "credit_code" else getattr(fake, option)()
                    if data not in temp_data:
                        temp_data.append(data)
                        i += 1
            all_data.append(temp_data)
        return app.restful.success("获取成功", data=[dict(zip(options, data)) for data in zip(*all_data)])


tool.add_url_rule("/makeUser", view_func=MakeUserInfoView.as_view("MakeUserInfoView"))
