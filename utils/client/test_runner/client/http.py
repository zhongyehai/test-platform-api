# -*- coding: utf-8 -*-
import copy
from datetime import datetime
from urllib import parse

import urllib3
import requests
from requests import Request, Response
from requests.exceptions import InvalidSchema, InvalidURL, MissingSchema, RequestException

from utils.util.file_util import FileUtil
from utils.client.test_runner import logger
from utils.client.test_runner.client import BaseSession
from utils.client.test_runner.utils import build_url, lower_dict_keys, omit_long_data

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ApiResponse(Response):

    def raise_for_status(self):
        """ Response中如果包含 error ，则抛出异常"""
        if hasattr(self, 'error') and self.error:
            raise self.error
        Response.raise_for_status(self)


# class HttpSession(requests.Session, BaseSession):
class HttpSession(BaseSession):
    """
    用于执行HTTP请求和在请求之间保持会话（cookie），以便能够登录和退出网站。
    每个请求都会被记录下来，这样TestRunner就可以显示统计数据。

    base_url为host，用于批量发请求时，拼接请求地址
    url允许只传接口地址，不传host，此时在发请求时会自动加上base_url
    """

    def __init__(self, base_url=None, *args, **kwargs):
        # super(HttpSession, self).__init__(*args, **kwargs)
        self.base_url = base_url if base_url else ""
        self.request_at = self.response_at = datetime.now()
        self.init_step_meta_data()

    def get_req_resp_record(self, resp_obj):
        """ 从response对象中获取请求和响应信息。 """
        # 把编码统一设为utf-8，防止响应体乱码
        resp_obj.encoding = 'utf-8'

        def log_print(req_resp_dict, r_type):
            msg = f"\n================== {r_type} 详细信息 ==================\n"
            for key, value in req_resp_dict[r_type].items():
                msg += "{:<16} : {}\n".format(key, repr(value))
            logger.log_debug(msg)

        req_resp_dict = {"request": {}, "response": {}}
        # req_resp_dict["extractors"] = resp_obj.extractors
        # record actual request info
        req_resp_dict["request"]["url"] = resp_obj.request.url
        req_resp_dict["request"]["method"] = resp_obj.request.method
        req_resp_dict["request"]["headers"] = dict(resp_obj.request.headers)

        request_body = resp_obj.request.body
        if request_body:
            request_content_type = lower_dict_keys(req_resp_dict["request"]["headers"]).get("content-type")
            if request_content_type and "multipart/form-data" in request_content_type:
                # 文件上传类型
                req_resp_dict["request"]["body"] = "upload file stream (OMITTED)"
            else:
                req_resp_dict["request"]["body"] = request_body

        log_print(req_resp_dict, "request")

        # 解析响应对象
        req_resp_dict["response"]["ok"] = resp_obj.ok
        req_resp_dict["response"]["url"] = resp_obj.url
        req_resp_dict["response"]["status_code"] = resp_obj.status_code
        req_resp_dict["response"]["reason"] = resp_obj.reason
        req_resp_dict["response"]["cookies"] = resp_obj.cookies or {}
        req_resp_dict["response"]["encoding"] = resp_obj.encoding
        resp_headers = dict(resp_obj.headers)
        req_resp_dict["response"]["headers"] = resp_headers

        lower_resp_headers = lower_dict_keys(resp_headers)
        content_type = lower_resp_headers.get("content-type", "")
        req_resp_dict["response"]["content_type"] = content_type

        if "image" in content_type:
            # 响应数据为图片，则存bytes数据流
            req_resp_dict["response"]["content"] = resp_obj.content
        else:
            try:
                # 响应体转json
                req_resp_dict["response"]["json"] = resp_obj.json()
            except ValueError:
                # 若不能转为json，则转为文本，默认最多512个字符
                resp_text = resp_obj.text
                req_resp_dict["response"]["text"] = omit_long_data(resp_text)

        log_print(req_resp_dict, "response")

        return req_resp_dict

    def send_client_request(self, method, url, name=None, case_id=None, variables_mapping={}, **kwargs):
        self.meta_data["name"] = name  # 记录测试名
        self.meta_data["case_id"] = case_id  # 步骤对应的用例id
        self.meta_data["variables_mapping"] = variables_mapping  # 记录发起此次请求时内存中的自定义变量

        # 记录原始的请求信息
        self.meta_data["data"][0]["request"]["method"] = method
        self.meta_data["data"][0]["request"]["url"] = url
        self.meta_data["data"][0]["request"].update(kwargs)

        # 构建请求的url
        url = build_url(self.base_url, url)

        copy_kwargs = copy.deepcopy(kwargs)  # 保留转码前的内容
        copy_kwargs["files"] = FileUtil.build_request_file(copy_kwargs["files"])  # 构建文件请求对象
        # 如果是 x-www-form-urlencoded 则进行转码
        if copy_kwargs.get("headers", {}).get("Content-Type", None) == 'application/x-www-form-urlencoded':
            # copy_kwargs["headers"].pop("Content-Type")
            copy_kwargs["data"] = parse.urlencode(copy_kwargs["data"])

        response = self._send_request_safe_mode(method, url, **copy_kwargs)  # 发送请求

        # requests包get响应内容中文乱码解决
        if response.content:
            response.encoding = response.apparent_encoding

        # 获取内容的长度，如果stream为True，则从响应头部获取，否则计算响应内容的长度
        if kwargs.get("stream", False):
            content_size = int(dict(response.headers).get("content-length") or 0)
        else:
            content_size = len(response.content or "")

        # 记录消耗的时间
        self.meta_data["stat"] = {
            "content_size": content_size,
            "elapsed_ms": round(response.elapsed.total_seconds() * 1000, 3),  # 请求耗时, 秒转毫秒
            "request_at": self.request_at.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "response_at": self.response_at.strftime("%Y-%m-%d %H:%M:%S.%f"),
        }
        # 记录请求和响应历史记录，包括 3x 的重定向
        # response_list = response.history + [response]
        # self.meta_data["data"] = [self.get_req_resp_record(resp_obj) for resp_obj in response_list]
        self.meta_data["data"] = [self.get_req_resp_record(response)]  # 不保存重定向数据
        self.meta_data["data"][0]["request"].update(kwargs)
        try:
            response.raise_for_status()
        except RequestException as e:
            logger.log_error(u"{exception}".format(exception=str(e)))
        else:
            logger.log_info(
                # f"""status_code: {response.status_code}, response_time(ms): {response_time_ms} ms, response_length: {content_size} bytes\n"""
                f"""步骤: {name}, 响应状态码: {response.status_code}, 耗时: {self.meta_data["stat"]["elapsed_ms"]} ms, response_length: {content_size} bytes\n"""
            )

        return response

    def _send_request_safe_mode(self, method, url, **kwargs):
        """ 发送HTTP请求，并捕获由于连接问题而可能发生的任何异常。 """
        try:
            self.request_at = datetime.now()
            # response = requests.Session.request(self, method, url, **kwargs)
            response = requests.request(method, url, **kwargs)
            self.response_at = datetime.now()
            return response
        except (MissingSchema, InvalidSchema, InvalidURL):
            raise
        except RequestException as ex:
            resp = ApiResponse()
            resp.error = ex
            resp.status_code = 0  # with this status_code, content returns None
            resp.request = Request(method, url).prepare()
            return resp
