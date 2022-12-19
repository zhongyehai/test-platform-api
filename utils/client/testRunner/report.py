# -*- coding: utf-8 -*-
import platform
import time
import unittest
from base64 import b64encode
from collections import Iterable

import requests

from . import logger
from .compat import basestring, json, numeric_types
from jinja2 import Template, escape


def get_system_platform():
    """ 系统信息 """
    return {
        "python_version": f"{platform.python_implementation()} {platform.python_version()}",
        "platform": platform.platform()
    }


def build_summary(result):
    """ 从测试结果中解析详细数据，用于渲染报告
    Args:
        result (instance): HtmlTestResult() instance
    Returns:
        dict: summary extracted from result.
            {
                "success": True,
                "stat": {},
                "time": {},
                "records": []
            }
    """
    success = result.wasSuccessful()
    total = result.testsRun
    failures = result.failures.__len__()
    errors = result.errors.__len__()
    skipped = result.skipped.__len__()
    expected_failures = result.expectedFailures.__len__()
    unexpected_successes = result.unexpectedSuccesses.__len__()

    return {
        "success": success,
        "stat": {
            'total': total,
            'failures': failures,
            'errors': errors,
            'skipped': skipped,
            'expectedFailures': expected_failures,
            'unexpectedSuccesses': unexpected_successes,
            'successes': total - failures - errors - skipped - expected_failures - unexpected_successes
        },
        "time": {
            'start_at': result.start_at,
            # 'start_date': result.start_date,
            'duration': result.duration
        },
        "records": result.records
    }


def merge_stat(origin_stat, new_stat):
    """ 合并stat """
    for key in new_stat:
        if key not in origin_stat:
            origin_stat[key] = new_stat[key]
        elif key == "start_at":
            origin_stat[key] = min(origin_stat[key], new_stat[key])
        else:
            origin_stat[key] += new_stat[key]


def format_summary(summary):
    """ 格式化测试结果数据，以便转储json文件并生成html报告。 """
    for index, suite_summary in enumerate(summary["details"]):

        if not suite_summary.get("name"):
            suite_summary["name"] = "testcase {}".format(index)

        for record in suite_summary.get("records"):
            meta_data = record['meta_datas']
            format_meta_data(meta_data)
            meta_data_expanded = []
            expand_meta_data(meta_data, meta_data_expanded)
            record["meta_datas_expanded"] = meta_data_expanded
            record["response_time"] = __get_total_response_time(meta_data_expanded)


def format_request(request_data: dict):
    """ 格式化http请求数据
    Args:
        request_data (dict): HTTP request data in dict.

            {
                "url": "http://127.0.0.1:5000/api/get-token",
                "method": "POST",
                "headers": {
                    "User-Agent": "python-requests/2.20.0",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept": "*/*",
                    "Connection": "keep-alive",
                    "user_agent": "iOS/10.3",
                    "device_sn": "TESTCASE_CREATE_XXX",
                    "os_platform": "ios",
                    "app_version": "2.8.6",
                    "Content-Type": "application/json",
                    "Content-Length": "52"
                },
                "json": {
                    "sign": "cb9d60acd09080ea66c8e63a1c78c6459ea00168"
                },
                "verify": false
            }

    """
    for key, value in request_data.items():

        if isinstance(value, list):
            value = json.dumps(value, indent=2, ensure_ascii=False)

        elif isinstance(value, bytes):
            try:
                encoding = "utf-8"
                value = escape(value.decode(encoding))
            except UnicodeDecodeError:
                pass

        elif not isinstance(value, (basestring, numeric_types, Iterable)):
            # class instance, e.g. MultipartEncoder()
            value = repr(value)

        elif isinstance(value, requests.cookies.RequestsCookieJar):
            value = value.get_dict()

        request_data[key] = value


def format_response(response_data: dict):
    """ 格式化http响应数据
    Args:
        response_data:
            {
                "status_code": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Content-Length": "30",
                    "Server": "Werkzeug/0.14.1 Python/3.7.0",
                    "Date": "Tue, 27 Nov 2018 06:19:27 GMT"
                },
                "encoding": "None",
                "content_type": "application/json",
                "ok": false,
                "url": "http://127.0.0.1:5000/api/users/9001",
                "reason": "NOT FOUND",
                "cookies": {},
                "json": {
                    "success": false,
                    "data": {}
                }
            }
    """
    for key, value in response_data.items():

        if isinstance(value, list):
            value = json.dumps(value, indent=2, ensure_ascii=False)

        elif isinstance(value, bytes):
            try:
                encoding = response_data.get("encoding")
                if not encoding or encoding == "None":
                    encoding = "utf-8"

                if key == "content" and "image" in response_data["content_type"]:
                    # display image
                    value = "data:{};base64,{}".format(
                        response_data["content_type"],
                        b64encode(value).decode(encoding)
                    )
                else:
                    value = escape(value.decode(encoding))
            except UnicodeDecodeError:
                pass

        elif not isinstance(value, (basestring, numeric_types, Iterable)):
            # class instance, e.g. MultipartEncoder()
            value = repr(value)

        elif isinstance(value, requests.cookies.RequestsCookieJar):
            value = value.get_dict()

        response_data[key] = value


def expand_meta_data(meta_data, meta_data_expanded):
    """ 扩展另一个列表中的字典
    Args:
        meta_data: [[dict1, dict2], dict3]
        meta_data_expanded: []
    Returns:
        [dict1, dict2, dict3]
    """
    if isinstance(meta_data, dict):
        meta_data_expanded.append(meta_data)
    elif isinstance(meta_data, list):
        for meta_data in meta_data:
            expand_meta_data(meta_data, meta_data_expanded)


def __get_total_response_time(meta_data_expanded):
    """ 计算所有元数据的总响应时间 """
    try:
        response_time = 0
        for meta_data in meta_data_expanded:
            response_time += meta_data["stat"]["response_time_ms"]

        return "{:.2f}".format(response_time)

    except TypeError:
        # failure exists
        return "N/A"


def format_meta_data(meta_data):
    if isinstance(meta_data, list):
        for _meta_data in meta_data:
            format_meta_data(_meta_data)
    elif isinstance(meta_data, dict):
        data_list = meta_data["data"]
        for data in data_list:
            format_request(data["request"])
            format_response(data["response"])


class HtmlTestResult(unittest.TextTestResult):
    """ 生成渲染html报告需要的测试结果数据 """

    def __init__(self, stream, descriptions, verbosity):
        super(HtmlTestResult, self).__init__(stream, descriptions, verbosity)
        self.start_at = None
        self.records = []

    def _record_test(self, test, status, attachment=''):
        self.records.append({
            'name': test.shortDescription(),
            'status': status,
            'attachment': attachment,
            "meta_datas": test.meta_datas
        })

    def startTestRun(self):
        """ 测试开始时间 """
        self.start_at = time.time()  # 时间戳格式，用于计算

    def startTest(self, test):
        """ 添加开始测试时间 """
        super(HtmlTestResult, self).startTest(test)
        logger.color_print(test.shortDescription(), "yellow")

    def addSuccess(self, test):
        """ 成功的用例 """
        super(HtmlTestResult, self).addSuccess(test)
        self._record_test(test, 'success')
        print("")

    def addError(self, test, err):
        """ 错误的用例 """
        super(HtmlTestResult, self).addError(test, err)
        self._record_test(test, 'error', self._exc_info_to_string(err, test))
        print("")

    def addFailure(self, test, err):
        """ 失败的用例 """
        super(HtmlTestResult, self).addFailure(test, err)
        self._record_test(test, 'failure', self._exc_info_to_string(err, test))
        print("")

    def addSkip(self, test, reason):
        """ 跳过的用例 """
        super(HtmlTestResult, self).addSkip(test, reason)
        self._record_test(test, 'skipped', reason)
        print("")

    def addExpectedFailure(self, test, err):
        super(HtmlTestResult, self).addExpectedFailure(test, err)
        self._record_test(test, 'ExpectedFailure', self._exc_info_to_string(err, test))
        print("")

    def addUnexpectedSuccess(self, test):
        super(HtmlTestResult, self).addUnexpectedSuccess(test)
        self._record_test(test, 'UnexpectedSuccess')
        print("")

    @property
    def duration(self):
        """ 用例耗时 """
        return round(time.time() - self.start_at, 4)
