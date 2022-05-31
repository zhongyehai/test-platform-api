# encoding: utf-8

""" 断言方法，函数注释不可改变，启动服务时会到这里来取名字做映射 """

import datetime
import json
import os
import random
import re
import string
import time

from pactverify.matchers import PactJsonVerify
from requests_toolbelt import MultipartEncoder

from .compat import basestring, builtin_str, integer_types
from .exceptions import ParamsError


def gen_random_string(str_len):
    """ 生成指定长度的随机字符串 """
    return ''.join(
        random.choice(string.ascii_letters + string.digits) for _ in range(str_len))


def get_timestamp(str_len=13):
    """ 获取0~16位的时间戳字符串 """
    if isinstance(str_len, integer_types) and 0 < str_len < 17:
        return builtin_str(time.time()).replace(".", "")[:str_len]
    raise ParamsError("时间戳字符串只能获取到0~16位")


def get_current_date(fmt="%Y-%m-%d"):
    """ 获取当前日期，默认格式为 %Y-%m-%d """
    return datetime.datetime.now().strftime(fmt)


def multipart_encoder(field_name, file_path, file_type=None, file_headers=None):
    if not os.path.isabs(file_path):
        file_path = os.path.join(os.getcwd(), file_path)

    filename = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        fields = {
            field_name: (filename, f.read(), file_type)
        }

    return MultipartEncoder(fields)


def multipart_content_type(multipart_encoder):
    return multipart_encoder.content_type


def _01equals(check_value, expect_value):
    """ 相等 """
    assert check_value == expect_value, '断言不通过，断言方式为相等'


def _02not_equals(check_value, expect_value):
    """ 不相等 """
    assert check_value != expect_value, '断言不通过，断言方式为不相等'


def _03json_equals(check_value, expect_value):
    """ json相等 """
    if isinstance(expect_value, str):
        expect_value = json.loads(expect_value)
    assert check_value == expect_value, '断言不通过，断言方式为json相等'


def _04contract_equals(check_value, expect_value):
    """ 契约校验 """
    # 详见：https://pypi.org/project/pactverify/
    if isinstance(expect_value, str):
        expect_value = json.loads(expect_value)
    pact_json_verify = PactJsonVerify(expect_value, hard_mode=True, separator='@')
    pact_json_verify.verify(check_value)  # 校验实际返回数据
    assert pact_json_verify.verify_result is True, json.dumps(pact_json_verify.verify_info, ensure_ascii=False, indent=4)


def _05contains(check_value, expect_value):
    """ 包含 """
    assert isinstance(check_value, (list, tuple, dict, basestring)), '实际结果非list, tuple, dict, str, 不能进行包含相关断言'
    assert expect_value in check_value, '实际结果不包含预期结果'


def _06not_contains(check_value, expect_value):
    """ 不包含 """
    assert isinstance(check_value, (list, tuple, dict, basestring)), '实际结果非list, tuple, dict, str, 不能进行包含相关断言'
    assert expect_value not in check_value


def _07included(check_value, expect_value):
    """ 被包含 """
    assert isinstance(check_value, (list, tuple, dict, basestring)), '实际结果非list, tuple, dict, str, 不能进行包含相关断言'
    assert check_value in expect_value


def _08not_included(check_value, expect_value):
    """ 不被包含 """
    assert isinstance(check_value, (list, tuple, dict, basestring)), '实际结果非list, tuple, dict, str, 不能进行包含相关断言'
    assert check_value not in expect_value


def _09string_equals(check_value, expect_value):
    """ 转为字符串以后相等 """
    assert builtin_str(check_value) == builtin_str(expect_value)


def _10string_included(check_value, expect_value):
    """ 转为字符串以后包含 """
    assert isinstance(expect_value, str), '预期结果只能为字符串'
    assert expect_value in builtin_str(check_value), '实际结果不包含预期结果'


def _11startswith(check_value, expect_value):
    """ 字符串的开头 """
    assert builtin_str(check_value).startswith(builtin_str(expect_value))


def _12endswith(check_value, expect_value):
    """ 字符串的结尾 """
    assert builtin_str(check_value).endswith(builtin_str(expect_value))


def _13is_true(check_value, expect_value=None):
    """ 值为真 """
    assert check_value


def _14is_not_true(check_value, expect_value=None):
    """ 值为假 """
    assert not check_value


def _15less_than(check_value, expect_value):
    """ 值小于 """
    assert check_value < expect_value


def _16less_than_or_equals(check_value, expect_value):
    """ 值小于等于 """
    assert check_value <= expect_value


def _17greater_than(check_value, expect_value):
    """ 值大于 """
    assert check_value > expect_value


def _18greater_than_or_equals(check_value, expect_value):
    """ 值大于等于 """
    assert check_value >= expect_value


def _19length_equals(check_value, expect_value):
    """ 长度等于 """
    assert isinstance(expect_value, integer_types)
    assert len(check_value) == expect_value


def _20length_greater_than(check_value, expect_value):
    """ 长度大于 """
    assert isinstance(expect_value, integer_types)
    assert len(check_value) > expect_value


def _21length_greater_than_or_equals(check_value, expect_value):
    """ 长度大于等于 """
    assert isinstance(expect_value, integer_types)
    assert len(check_value) >= expect_value


def _22length_less_than(check_value, expect_value):
    """ 长度小于 """
    assert isinstance(expect_value, integer_types)
    assert len(check_value) < expect_value


def _23length_less_than_or_equals(check_value, expect_value):
    """ 长度小于等于 """
    assert isinstance(expect_value, integer_types)
    assert len(check_value) <= expect_value


def _24type_match(check_value, expect_value):
    """ 断言数据类型 """

    def get_type(name):
        if isinstance(name, type):
            return name
        elif isinstance(name, basestring):
            try:
                return __builtins__[name]
            except KeyError:
                raise ValueError(name)
        else:
            raise ValueError(name)

    assert isinstance(check_value, get_type(expect_value))


def _25regex_match(check_value, expect_value):
    """ 正则匹配 """
    assert isinstance(expect_value, basestring)
    assert isinstance(check_value, basestring)
    assert re.match(expect_value, check_value)
