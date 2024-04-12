# -*- coding: utf-8 -*-
import os
import email
import platform
from urllib import parse

import urllib3.fields as f
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from utils.client.test_runner import built_in as assert_func_file
from utils.client.test_runner.webdriver_action import Actions

_basedir = os.path.abspath(".")
_main_server_port = 8024  # 主程序端口
_main_server_host = f'http://localhost:{_main_server_port}'  # 主程序后端服务
_job_server_port = 8025  # job服务端口
_job_server_host = f'http://localhost:{_job_server_port}/api/job/status'  # job服务接口
_admin_default_password = "123456"
# 默认的webhook地址，用于接收系统状态通知、系统异常/错误通知...
_default_web_hook_type = 'ding_ding'  # 默认通知的webhook类型，见枚举类apps.enums.WebHookTypeEnum
_default_web_hook = ''
_web_hook_secret = ''  # secret，若是关键词模式，不用设置

platform_name = "极测平台"  # 测试平台名字
is_linux = platform.platform().startswith('Linux')
# 从 testRunner.built_in 中获取断言方式并映射为字典和列表，分别给前端和运行测试用例时反射断言
assert_mapping, assert_mapping_list = {}, []
for func in dir(assert_func_file):
    if func.startswith("_") and not func.startswith("__"):
        doc = getattr(assert_func_file, func).__doc__.strip()  # 函数注释
        assert_mapping.setdefault(doc, func)
        assert_mapping_list.append({"value": doc})

# UI自动化的行为事件
action_mapping = Actions.get_action_mapping()
ui_action_mapping_dict, ui_action_mapping_list = action_mapping["mapping_dict"], action_mapping["mapping_list"]
ui_action_mapping_reverse = dict(zip(ui_action_mapping_dict.values(), ui_action_mapping_dict.keys()))

# UI自动化的断言事件
ui_assert_mapping = Actions.get_assert_mapping()
ui_assert_mapping_dict, ui_assert_mapping_list = ui_assert_mapping["mapping_dict"], ui_assert_mapping["mapping_list"]

# UI自动化的数据提取事件
extract_mapping = Actions.get_extract_mapping()
ui_extract_mapping, ui_extract_mapping_list = extract_mapping["mapping_dict"], extract_mapping["mapping_list"]
ui_extract_mapping.setdefault("自定义函数", "func")
ui_extract_mapping_list.extend([
    {"label": "常量", "value": "const"},
    {"label": "自定义变量", "value": "variable"},
    {"label": "自定义函数", "value": "func"}
])

# 跳过条件判断类型映射
skip_if_type_mapping = [
    {"label": "且", "value": "and"},
    {"label": "或", "value": "or"}
]

# 测试类型
test_type = [
    {"key": "api", "label": "接口测试"},
    {"key": "app", "label": "app测试"},
    {"key": "ui", "label": "ui测试"}
]

# 运行测试的类型
run_type = {
    "api": "接口",
    "case": "用例",
    "suite": "用例集",
    "task": "任务",
}

# 执行模式
run_model = {0: "串行执行", 1: "并行执行"}

# 请求方法
http_method = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

# 创建项目/服务时，默认要同时创建的用例集列表
api_suite_list = [
    {"key": "base", "value": "基础用例集"},
    {"key": "quote", "value": "引用用例集"},
    {"key": "api", "value": "单接口用例集"},
    {"key": "process", "value": "流程用例集"},
    {"key": "make_data", "value": "造数据用例集"}
]

ui_suite_list = [
    {"key": "base", "value": "基础用例集"},
    {"key": "quote", "value": "引用用例集"},
    {"key": "process", "value": "流程用例集"},
    {"key": "make_data", "value": "造数据用例集"}
]

# 元素定位方式
find_element_option = [
    {"label": "根据id属性定位", "value": "id"},
    {"label": "根据xpath表达式定位", "value": "xpath"},
    {"label": "根据class选择器定位", "value": "class name"},
    {"label": "根据css选择器定位", "value": "css selector"},
    {"label": "根据name属性定位", "value": "name"},
    {"label": "根据tag名字定位 ", "value": "tag name"},
    {"label": "根据超链接文本定位", "value": "link text"},
    {"label": "页面地址", "value": "url"},
    {"label": "坐标定位(APP)", "value": "coordinate"}
]

# 数据提取类型
extracts_mapping = [
    {"label": "响应体", "value": "content"},
    {"label": "响应头部信息", "value": "headers"},
    {"label": "响应cookies", "value": "cookies"},
    {"label": "正则表达式（从响应体提取）", "value": "regexp"},
    {"label": "常量", "value": "const"},
    {"label": "自定义变量", "value": "variable"},
    {"label": "自定义函数", "value": "func"},
    {"label": "其他（常量、自定义变量、自定义函数）", "value": "other"}
]

# python数据类型
data_type_mapping = [
    {"label": "普通字符串", "value": "str"},
    {"label": "json字符串", "value": "json"},
    {"label": "整数", "value": "int"},
    {"label": "小数", "value": "float"},
    {"label": "列表", "value": "list"},
    {"label": "字典", "value": "dict"},
    {"label": "空值(null)", "value": "None"},
    {"label": "布尔值True", "value": "True"},
    {"label": "布尔值False", "value": "False"},
    {"label": "自定义函数", "value": "func"},
    {"label": "自定义变量", "value": "variable"},
    {"label": "文件", "value": "file"}
]

# ui自动化支持的浏览器
browser_name = {
    "chrome": "chrome",
    # "gecko": "火狐"
}

# 运行app自动化的服务器设备系统映射
server_os_mapping = ["Windows", "Mac", "Linux"]

# 运行app自动化的手机设备系统映射
phone_os_mapping = ["Android", "iOS"]

# APP模拟键盘输入的code
app_key_board_code = {
    "7": "按键'0'",
    "8": "按键'1'",
    "9": "按键'2'",
    "10": "按键'3'",
    "11": "按键'4'",
    "12": "按键'5'",
    "13": "按键'6'",
    "14": "按键'7'",
    "15": "按键'8'",
    "16": "按键'9'",
    "29": "按键'A'",
    "30": "按键'B'",
    "31": "按键'C'",
    "32": "按键'D'",
    "33": "按键'E'",
    "34": "按键'F'",
    "35": "按键'G'",
    "36": "按键'H'",
    "37": "按键'I'",
    "38": "按键'J'",
    "39": "按键'K'",
    "40": "按键'L'",
    "41": "按键'M'",
    "42": "按键'N'",
    "43": "按键'O'",
    "44": "按键'P'",
    "45": "按键'Q'",
    "46": "按键'R'",
    "47": "按键'S'",
    "48": "按键'T'",
    "49": "按键'U'",
    "50": "按键'V'",
    "51": "按键'W'",
    "52": "按键'X'",
    "53": "按键'Y'",
    "54": "按键'Z'",
    "4": "返回键",
    "5": "拨号键",
    "6": "挂机键",
    "82": "菜单键",
    "3": "home键",
    "27": "拍照键"
}

# faker 造数据方法映射
make_user_info_mapping = {
    "name": "姓名",
    "ssn": "身份证号",
    "phone_number": "手机号",
    "credit_card_number": "银行卡",
    "address": "地址",
    "company": "公司名",
    "credit_code": "统一社会信用代码",
    "company_email": "公司邮箱",
    "job": "工作",
    "ipv4": "ipv4地址",
    "ipv6": "ipv6地址"
}

# faker 造数据语言映射
make_user_language_mapping = {
    'zh_CN': '简体中文',
    'en_US': '英语-美国',
    'ja_JP': '日语-日本',
    'hi_IN': '印地语-印度',
    'ko_KR': '朝鲜语-韩国',
    'es_ES': '西班牙语-西班牙',
    'pt_PT': '葡萄牙语-葡萄牙',
    'es_MX': '西班牙语-墨西哥',
    # 'ar_EG': '阿拉伯语-埃及',
    # 'ar_PS': '阿拉伯语-巴勒斯坦',
    # 'ar_SA': '阿拉伯语-沙特阿拉伯',
    # 'bg_BG': '保加利亚语-保加利亚',
    # 'cs_CZ': '捷克语-捷克',
    # 'de_DE': '德语-德国',
    # 'dk_DK': '丹麦语-丹麦',
    # 'el_GR': '希腊语-希腊',
    # 'en_AU': '英语-澳大利亚',
    # 'en_CA': '英语-加拿大',
    # 'en_GB': '英语-英国',
    # 'et_EE': '爱沙尼亚语-爱沙尼亚',
    # 'fa_IR': '波斯语-伊朗',
    # 'fi_FI': '芬兰语-芬兰',
    # 'fr_FR': '法语-法国',
    # 'hr_HR': '克罗地亚语-克罗地亚',
    # 'hu_HU': '匈牙利语-匈牙利',
    # 'hy_AM': '亚美尼亚语-亚美尼亚',
    # 'it_IT': '意大利语-意大利',
    # 'ka_GE': '格鲁吉亚语-格鲁吉亚',
    # 'lt_LT': '立陶宛语-立陶宛',
    # 'lv_LV': '拉脱维亚语-拉脱维亚',
    # 'ne_NP': '尼泊尔语-尼泊尔',
    # 'nl_NL': '德语-荷兰',
    # 'no_NO': '挪威语-挪威',
    # 'pl_PL': '波兰语-波兰',
    # 'pt_BR': '葡萄牙语-巴西',
    # 'ru_RU': '俄语-俄国',
    # 'sl_SI': '斯诺文尼亚语-斯诺文尼亚',
    # 'sv_SE': '瑞典语-瑞典',
    # 'tr_TR': '土耳其语-土耳其',
    # 'uk_UA': '乌克兰语-乌克兰',
    # 'zh_TW': '繁体中文'
}


def my_format_header_param(name, value):
    if not any(ch in value for ch in '"\\\r\n'):
        result = '%s="%s"' % (name, value)
        try:
            result.encode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
        else:
            return result
    value = email.utils.encode_rfc2231(value, "utf-8")
    value = "%s*=%s" % (name, value)
    return value


# 猴子补丁，修复request上传文件时，不能传中文
f.format_header_param = my_format_header_param


class _Sso:
    """ 身份验证如果是走SSO，则以下配置项必须正确 """
    sso_host = "http://www.xxx.com"
    sso_authorize_endpoint = "/oauth2/authorize"
    sso_token_endpoint = "/oauth2/token"
    client_id = "xxx"
    client_secret = "xxx"
    redirect_uri = "http://www.xxx.com/sso/login"  # 测试平台SSO登录的前端地址
    front_redirect_addr = (f"{sso_host}{sso_authorize_endpoint}?"
                           f"response_type=code&"
                           f"client_id={client_id}&"
                           f"scope=openid profile&"
                           f"state=xxx&"
                           f"redirect_uri={redirect_uri}&"
                           f"nonce=xxx")


class _SystemConfig:
    AUTH_TYPE = 'test_platform'  # 身份验证机制 OSS, test_platform
    SSO = _Sso
    ACCESS_TOKEN_TIME_OUT = 0.5 * 60 * 60  # access_token 有效期，2个小时
    REFRESH_TOKEN_TIME_OUT = 7 * 24 * 60 * 60  # refresh_token 有效期，7天
    SECRET_KEY = "localhost"
    URL_NOT_FIND_MSG = None  # 统一自定义404消息，若没有对应使用场景设为None即可

    # 数据库信息
    DB_HOST = "localhost"
    DB_PORT = 3306
    DB_USER = "root"
    DB_PASSWORD = ""
    DB_DATABASE = ""

    # 数据库链接
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{parse.quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}?autocommit=true"

    # 关闭数据追踪，避免内存资源浪费
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 关闭自动提交，若开启自动提交会出现以下报错
    # sqlalchemy.exc.InvalidRequestError: Can"t reconnect until invalid transaction is rolled back
    SQLALCHEMY_COMMIT_ON_TEARDOWN = False

    # 每次连接从池中检查，如果有错误，监测为断开的状态，连接将被立即回收。
    SQLALCHEMY_POOL_PRE_PING = True

    # 数据库连接池的大小。默认是数据库引擎的默认值默认是5
    SQLALCHEMY_POOL_SIZE = 200

    # 当连接池达到最大值后可以创建的连接数。当这些额外的连接处理完回收后，若没有在等待进程获取连接，这个连接将会被立即释放。
    SQLALCHEMY_MAX_OVERFLOW = 1000

    # 从连接池里获取连接
    # 如果此时无空闲的连接，且连接数已经到达了pool_size+max_overflow。此时获取连接的进程会等待pool_timeout秒。
    # 如果超过这个时间，还没有获得将会抛出异常。
    # 默认是30秒
    SQLALCHEMY_POOL_TIMEOUT = 30

    # 一个数据库连接的生存时间。
    #     例如pool_recycle=3600。也就是当这个连接产生1小时后，再获得这个连接时，会丢弃这个连接，重新创建一个新的连接。
    #
    # 当pool_recycle设置为-1时，也就是连接池不会主动丢弃这个连接。永久可用。但是有可能数据库server设置了连接超时时间。
    #     例如mysql，设置的有wait_timeout默认为28800，8小时。当连接空闲8小时时会自动断开。8小时后再用这个连接也会被重置。
    SQLALCHEMY_POOL_RECYCLE = 3600  # 1个小时

    # 输出SQL语句
    # SQLALCHEMY_ECHO = True

    # flask_apscheduler 定时任务存储配置
    SCHEDULER_JOBSTORES = {
        "default": SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URI)
    }
    # flask_apscheduler 线程池配置
    SCHEDULER_EXECUTORS = {
        "default": {"type": "threadpool", "max_workers": 20}
    }
    SCHEDULER_JOB_DEFAULTS = {
        "coalesce": False,
        "max_instances": 2,
        "misfire_grace_time": None
    }
    SCHEDULER_TIMEZONE = "Asia/Shanghai"  # 时区
    SCHEDULER_API_ENABLED = True  # 开启API访问功能
    SCHEDULER_API_PREFIX = "/api/scheduler"  # api前缀（默认是/scheduler）


if __name__ == "__main__":
    pass
