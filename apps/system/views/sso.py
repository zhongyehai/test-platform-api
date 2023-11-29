# -*- coding: utf-8 -*-
""" SSO方式 登录 """
import base64
import json

from flask import current_app as app, request
import requests

from ..blueprint import system_manage
from ..model_factory import User, Role, UserRoles
from ...config.model_factory import BusinessLine
from utils.logs.log import logger

def base64_url_decode(inp):
    padding = '=' * (4 - (len(inp) % 4))
    return base64.urlsafe_b64decode(inp + padding)


def parse_sso_id_token(id_token):
    """ 根据id_token解析用户信息 """
    header, payload, signature = id_token.split('.')
    token_header, token_payload = json.loads(base64_url_decode(header)), json.loads(base64_url_decode(payload))
    return {"user_id": token_payload["sub"], "user_name": token_payload["user_name"]}


def get_sso_server_info():
    """ 获取sso相关信息 """
    res = requests.get(url=f'{app.config["OSS"].oss_host}/.well-known/openid-configuration').json()
    return {
        "authorization_endpoint": res["authorization_endpoint"], "token_endpoint": res["token_endpoint"],
        "userinfo_endpoint": res["userinfo_endpoint"], "jwks_uri": res["jwks_uri"]
    }


def get_sso_token(code):
    """ 从sso服务器获取用户token """
    res = requests.post(
        url=f'{app.config["OSS"].oss_host}{app.config["OSS"].oss_token_endpoint}',
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": app.config["OSS"].client_id,
            "client_secret": app.config["OSS"].client_secret,
            "redirect_uri": app.config["OSS"].redirect_uri
        }
    )
    logger.info(f'get_sso_token.res.text: \n{res.text}')
    return res.json()


@system_manage.get("/sso/redirect-uri")
def system_manage_get_sso_redirect_uri():
    """ 返回重定向的登录地址 """
    return app.restful.success(app.config["OSS"].front_redirect_addr if app.config["AUTH_TYPE"] == "SSO" else None)


@system_manage.post("/sso/token")
def system_manage_get_token():
    """ 返回重定向的登录地址 """

    # 根据接收到的code，获取token
    sso_token = get_sso_token(request.json.get("code"))

    # 解析token
    user_info = parse_sso_id_token(sso_token["id_token"])
    sso_user_id, sso_user_name = user_info["user_id"], user_info["user_name"]

    user = User.query.filter_by(sso_user_id=sso_user_id, name=sso_user_name).first()
    if not user:  # 数据库中没有这个用户，需插入一条数据，再生成token
        user = User.query.filter_by(name=sso_user_name).first()
        if user:
            user.model_update({"sso_user_id": sso_user_id})
        else:
            # 新增用户，默认为公共业务线权限
            common_id = BusinessLine.db.session.query(BusinessLine.id).filter(BusinessLine.code == "common").first()
            user = User.model_create_and_get({
                "sso_user_id": sso_user_id, "name": sso_user_name, "business_list": [common_id], "password": "123456"
            })
            # 角色为测试人员
            role_id = Role.db.session.query(Role.id).filter(Role.name == "测试人员").first()
            UserRoles.model_create({"user_id": user.id, "role_id": role_id})

    # 根据用户id信息生成token，并返回给前端
    user_info = user.to_dict()
    user_permissions = user.get_permissions()
    user_info["token"] = user.make_token(user_permissions["api_addr_list"])
    user_info["front_permissions"] = user_permissions["front_addr_list"]
    return app.restful.success("登录成功", user_info)