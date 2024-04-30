# -*- coding: utf-8 -*-
""" SSO方式 登录 """
from flask import current_app as app, request
import requests

from ..blueprint import system_manage
from ..model_factory import User, Role, UserRoles
from ...config.model_factory import BusinessLine
from utils.logs.log import logger
from utils.parse.parse_token import parse_token


def get_sso_server_info():
    """ 获取sso相关信息 """
    res = requests.get(url=f'{app.config["OSS"].oss_host}/.well-known/openid-configuration').json()
    return {
        "authorization_endpoint": res["authorization_endpoint"], "token_endpoint": res["token_endpoint"],
        "userinfo_endpoint": res["userinfo_endpoint"], "jwks_uri": res["jwks_uri"]
    }


def get_sso_token(code):
    """ 从sso服务器获取用户token """
    sso_config = app.config["SSO"]
    url = f'{sso_config.sso_host}{sso_config.sso_token_endpoint}'
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": sso_config.client_id,
        "client_secret": sso_config.client_secret,
        "redirect_uri": sso_config.redirect_uri
    }
    logger.info(f'get_sso_token: \nurl: {url}, \ndata: {data}')
    res = requests.post(url=url, data=data)
    logger.info(f'get_sso_token.res.text: \n{res.text}')
    return res.json()


@system_manage.get("/sso/redirect-uri")
def system_manage_get_sso_redirect_uri():
    """ 返回重定向的登录地址 """
    return app.restful.not_login(app.config["SSO"].front_redirect_addr if app.config["AUTH_TYPE"] == "SSO" else None)


@system_manage.post("/sso/token")
def system_manage_get_token():
    """ 返回重定向的登录地址 """

    # 根据接收到的code，获取token
    sso_token = get_sso_token(request.json.get("code"))

    # 解析token
    payload = parse_token(sso_token["id_token"])["payload"]
    sso_user_id, sso_user_name = payload.get("sub"), payload.get("user_name")
    phone_number, email = payload.get("phoneNumber"), payload.get("email")

    user = User.query.filter_by(sso_user_id=sso_user_id, name=sso_user_name).first()
    if not user:  # 数据库中没有这个用户，需插入一条数据，再生成token
        user = User.query.filter_by(sso_user_id=None, name=sso_user_name).first()
        if user:
            user.model_update({"sso_user_id": sso_user_id, "email": email, "phone_number": phone_number})
        else:
            # 新增用户，默认为公共业务线权限
            common_id = BusinessLine.db.session.query(BusinessLine.id).filter(BusinessLine.code == "common").first()
            user = User.model_create_and_get({
                "sso_user_id": sso_user_id,
                "name": sso_user_name,
                "phone_number": phone_number,
                "email": email,
                "business_list": [common_id[0]],
                "password": "123456"
            })
            # 角色为测试人员
            role_id = Role.db.session.query(Role.id).filter(Role.name == "测试人员").first()
            UserRoles.model_create({"user_id": user.id, "role_id": role_id[0]})
    else:  # 历史数据，如果没有手机号，需要更新一下
        if user.phone_number is None:
            user.model_update({"email": email, "phone_number": phone_number})

    # 根据用户id信息生成token，并返回给前端
    user_info = user.build_access_token()
    user_info["refresh_token"] = user.make_refresh_token()
    return app.restful.success("登录成功", user_info)
