# -*- coding: utf-8 -*-
from flask import current_app as app, request

from apps.tools.blueprint import tool
from utils.parse.parse_token import parse_token


@tool.post("/parse-token")
def tool_parse_token():
    """ 解析token """
    token_str = request.json.get("token")
    if token_str is None:
        return app.restful.fail("token 字符串必传")
    try:
        return app.restful.get_success(parse_token(token_str))
    except Exception as e:
        return app.restful.fail("token 解析失败，请检查token字符串是否正确")
