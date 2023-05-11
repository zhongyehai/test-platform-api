# -*- coding: utf-8 -*-
import json
import os.path

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from utils.util.jsonUtil import JsonUtil
from app.baseModel import db
from app.system.models.user import User, Permission, Role, RolePermissions, UserRoles
from app.config.models.config import Config, ConfigType
from app.config.models.runEnv import RunEnv
from app.config.models.business import BusinessLine
from app.assist.models.script import Script
from main import app

manager = Manager(app)

Migrate(app, db)
manager.add_command("db", MigrateCommand)


def print_start_delimiter(content):
    print(f'{"*" * 20} {content} {"*" * 20}')


def print_type_delimiter(content):
    print(f'    {"=" * 16} {content} {"=" * 16}')


def print_item_delimiter(content):
    print(f'        {"=" * 12} {content} {"=" * 12}')


def print_detail_delimiter(content):
    print(f'            {"=" * 8} {content} {"=" * 8}')


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

kym_keyword = [
    {
        "topic": "使用群体",
        "children": [
            {"topic": "产品使用群体是哪些？"},
            {"topic": "用户与用户之间有什么关联？"},
            {"topic": "用户为什么提这个需求？"},
            {"topic": "用户为什么提这个需求？"},
            {"topic": "用户最关心的是什么？"},
            {"topic": "用户的实际使用环境是什么？"}
        ]
    },
    {
        "topic": "里程碑",
        "children": [
            {"topic": "需求评审时间？"},
            {"topic": "开发提测时间？"},
            {"topic": "测试周期测试时间多长？"},
            {"topic": "轮次安排进行几轮测试？"},
            {"topic": "UAT验收时间？"},
            {"topic": "上线时间？"}
        ]
    },
    {
        "topic": "涉及人员",
        "children": [
            {"topic": "负责迭代的产品是谁？"},
            {"topic": "后端开发是谁经验如何？"},
            {"topic": "前端开发是谁经验如何？"},
            {"topic": "测试人员是谁？"}
        ]
    },
    {
        "topic": "涉及模块",
        "children": [
            {"topic": "项目中涉及哪些模块，对应的开发责任人是谁？"}
        ]
    },
    {
        "topic": "项目信息",
        "children": [
            {"topic": "项目背景是什么？"},
            {"topic": "这个项目由什么需要特别注意的地方？"},
            {"topic": "可以向谁进一步了解项目信息？"},
            {"topic": "有没有文档、手册、材料等可供参考？"},
            {"topic": "这是全新的产品还是维护升级的？"},
            {"topic": "有没有竞品分析结果或同类产品可供参考？"},
            {"topic": "历史版本曾今发生过那些重大故障？"}
        ]
    },
    {
        "topic": "测试信息",
        "children": [
            {"topic": "会使用到的测试账号有哪些？"},
            {"topic": "会用到的测试地址？"},
            {"topic": "有没有不太熟悉、掌握的流程？"}
        ]
    },
    {
        "topic": "设备工具",
        "children": [
            {"topic": "测试过程中是否会用到其他测试设备资源是否够（Ukey、手机、平板）？"},
            {"topic": "会用到什么测试工具会不会使用？"}
        ]
    },
    {
        "topic": "测试团队",
        "children": [
            {"topic": "有几个测试团队负责测试？"},
            {"topic": "负责测试的人员组成情况？"},
            {"topic": "测试人员的经验如何？"},
            {"topic": "测试人员对被测对象的熟悉程度如何？"},
            {"topic": "测试人员是专职的还是兼职的？"},
            {"topic": "测试人手是否充足？"}
        ]
    },
    {
        "topic": "测试项",
        "children": [
            {"topic": "主要的测试内容有哪些？"},
            {"topic": "哪部分可以降低优先级或者先不测试？"},
            {"topic": "哪些内容是新增或修改？"},
            {"topic": "是否涉及历史数据迁移测试？"},
            {"topic": "是否涉及与外系统联调测试？"},
            {"topic": "是否需要进行性能、兼容性、安全测试？"}
        ]
    }
]

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

# 模拟键盘输入的code
app_key_code = {
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
    "54": "按键'Z'"
}

# 默认分页信息
pagination_size = {
    "page_num": 1,
    "page_size": 20,
}

# 响应数据源
response_data_source_mapping = [
    {"label": "响应体", "value": "content"},
    {"label": "响应头部信息", "value": "headers"},
    {"label": "响应cookies", "value": "cookies"},
    {"label": "正则表达式（从响应体提取）", "value": "regexp"},
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
    {"label": "布尔值True", "value": "true"},
    {"label": "布尔值False", "value": "false"},
    {"label": "自定义函数", "value": "func"},
    {"label": "自定义变量", "value": "variable"}
]

# ui自动化支持的浏览器
browser_name = {
    "chrome": "chrome",
    "gecko": "火狐"
}

# ui自动化元素定位方式
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

# 运行测试的类型
run_type = {
    "api": "接口",
    "case": "用例",
    "suite": "用例集",
    "task": "任务",
}

# 测试类型
test_type = [
    {"key": "api", "label": "接口测试"},
    {"key": "appUi", "label": "app测试"},
    {"key": "webUi", "label": "ui测试"}
]

# 运行app自动化的服务器设备系统映射
server_os_mapping = ["Windows", "Mac", "Linux"]

# 运行app自动化的手机设备系统映射
phone_os_mapping = ["Android", "iOS"]

# 创建项目/服务时，默认要同时创建的用例集列表
api_suite_list = [
    {"key": "base", "value": "基础用例集"},
    {"key": "quote", "value": "引用用例集"},
    {"key": "api", "value": "单接口用例集"},
    {"key": "process", "value": "流程用例集"},
    {"key": "assist", "value": "造数据用例集"}
]
ui_suite_list = [
    {"key": "base", "value": "基础用例集"},
    {"key": "quote", "value": "引用用例集"},
    {"key": "process", "value": "流程用例集"},
    {"key": "assist", "value": "造数据用例集"}
]

# 回调流水线消息内容
call_back_msg_addr = ""

# 保存脚本时，不校验格式的函数名字
name_list = ["contextmanager"]

with open('rules.json', 'r', encoding='utf8') as rules:
    permission_dict = json.load(rules)


@manager.command
def init_permission():
    """ 初始化权限 """
    print_type_delimiter("开始创建权限")

    for source_type, permission_rules in permission_dict.items():
        for rule_type, rule_list in permission_rules.items():
            for rule in rule_list:
                if Permission.get_first(source_addr=rule["source_addr"], source_type=source_type) is None:
                    rule["source_type"] = source_type
                    rule["source_class"] = "menu" if rule["source_addr"] != "admin" else "admin"
                    Permission().create(rule)
                    print_type_delimiter(f'权限【{rule["name"]}】创建成功')
    print_type_delimiter("权限创建完成")


@manager.command
def init_role():
    """ 初始化角色和对应的权限 """
    print_type_delimiter("开始创建角色")

    print_type_delimiter("开始创建【后端管理员】角色")
    if Role.get_first(name="管理员-后端") is None:
        admin_role = Role().create({"name": "管理员-后端", "desc": "后端管理员, 有权限访问任何接口"})
        admin_permission = Permission.get_first(source_addr='admin', source_type='api')
        RolePermissions().create({"role_id": admin_role.id, "permission_id": admin_permission.id})
    print_type_delimiter("【后端管理员】创建完成")

    print_type_delimiter("开始创建【前端管理员】角色")
    if Role.get_first(name="管理员-前端") is None:
        admin_role = Role().create({"name": "管理员-前端", "desc": "前端管理员, 有权限访问任何页面、按钮"})
        admin_permission = Permission.get_first(source_addr='admin', source_type='front')
        RolePermissions().create({"role_id": admin_role.id, "permission_id": admin_permission.id})
    print_type_delimiter("【前端管理员】创建完成")

    print_type_delimiter("开始创建测试人员角色")
    if Role.get_first(name="测试人员") is None:
        test_role = Role().create({"name": "测试人员", "desc": "能访问项目的基本信息，不能访问配置管理"})
        for source_type, permission_rules in permission_dict.items():
            if source_type == "front":
                for rule_type, source_addr_list in permission_rules.items():
                    for source in source_addr_list:
                        addr = source["source_addr"]
                        if addr.startswith(('/system', '/config', '/help', 'admin')) is False and "task" not in addr:
                            permission = Permission.get_first(source_addr=addr)
                            RolePermissions().create({"role_id": test_role.id, "permission_id": permission.id})
    print_type_delimiter("测试人员角色创建完成")

    print_type_delimiter("开始创建项目负责人角色")
    if Role.get_first(name="项目负责人") is None:
        test_role = Role.get_first(name="测试人员")
        manager_role = Role().create({
            "name": "项目负责人",
            "desc": "有权限访问项目的任何页面、按钮和配置管理",
            "extend_role": [test_role.id]
        })
        for source_type, permission_rules in permission_dict.items():
            if source_type == "front":
                for rule_type, source_addr_list in permission_rules.items():
                    for source in source_addr_list:
                        addr = source["source_addr"]
                        if addr.startswith('/config'):
                            permission = Permission.get_first(source_addr=addr)
                            RolePermissions().create({"role_id": manager_role.id, "permission_id": permission.id})
    print_type_delimiter("项目负责人角色创建完成")

    print_type_delimiter("角色创建完成")


@manager.command
def init_user():
    """ 初始化用户和对应的角色 """

    # 创建业务线
    print_type_delimiter("开始创建业务线")
    business_dict = {"name": "公共业务线", "code": "common", "desc": "公共业务线，所有人都可见、可操作", "num": 0}
    business = BusinessLine.get_first(code=business_dict["code"])
    if business is None:
        business_dict["env_list"] = [run_env.id for run_env in RunEnv.get_all()]
        business = BusinessLine().create(business_dict)
        print_item_delimiter(f'业务线【{business.name}】创建成功')
    print_type_delimiter("业务线创建完成")

    # 创建用户
    print_type_delimiter("开始创建用户")
    user_list = [
        {"account": "admin", "password": "123456", "name": "管理员", "role": ["管理员-后端", "管理员-前端"]},
        {"account": "manager", "password": "manager", "name": "项目负责人", "role": ["项目负责人"]},
        {"account": "common", "password": "common", "name": "测试员", "role": ["测试人员"]}
    ]
    for user_info in user_list:
        if User.get_first(account=user_info["account"]) is None:
            user_info["status"] = 1
            user_info["business_list"] = [business.id]
            user = User().create(user_info)
            for role_name in user_info["role"]:
                role = Role.get_first(name=role_name)
                UserRoles().create({"user_id": user.id, "role_id": role.id})
            print_item_delimiter(f'用户【{user_info["name"]}】创建成功')

    print_type_delimiter("用户创建完成")


@manager.command
def init_config_type():
    """ 初始化配置类型 """
    print_type_delimiter("开始创建配置类型")
    config_type_list = [
        {"name": "系统配置", "desc": "全局配置"},
        {"name": "邮箱", "desc": "邮箱服务器"},
        {"name": "接口自动化", "desc": "接口自动化测试"},
        {"name": "webUi自动化", "desc": "webUi自动化测试"},
        {"name": "appUi自动化", "desc": "appUi自动化测试"}
    ]
    for data in config_type_list:
        if ConfigType.get_first(name=data["name"]) is None:
            ConfigType().create(data)
            print_item_delimiter(f'配置类型【{data["name"]}】创建成功')
    print_type_delimiter("配置类型创建完成")


@manager.command
def init_config():
    """ 初始化配置 """

    print_type_delimiter("开始创建配置")

    # 配置
    type_dict = {config_type.name: config_type.id for config_type in ConfigType.get_all()}  # 所有配置类型
    conf_dict = {
        "邮箱": [
            {"name": "QQ邮箱", "value": "smtp.qq.com", "desc": "QQ邮箱服务器"}
        ],

        "系统配置": [
            {"name": "platform_name", "value": "极测平台", "desc": "测试平台名字"},
            {"name": "run_type", "value": JsonUtil.dumps(run_type), "desc": "运行测试的类型"},
            {"name": "data_type_mapping", "value": JsonUtil.dumps(data_type_mapping), "desc": "python数据类型映射"},
            {"name": "yapi_host", "value": "", "desc": "yapi域名"},
            {"name": "yapi_account", "value": "", "desc": "yapi账号"},
            {"name": "yapi_password", "value": "", "desc": "yapi密码"},
            {"name": "ignore_keyword_for_group", "value": "[]", "desc": "不需要从yapi同步的分组关键字"},
            {"name": "ignore_keyword_for_project", "value": "[]", "desc": "不需要从yapi同步的服务关键字"},
            {"name": "kym", "value": JsonUtil.dumps(kym_keyword), "desc": "KYM分析项"},
            {"name": "sync_mock_data", "value": JsonUtil.dumps({}), "desc": "同步回调数据源"},
            {"name": "async_mock_data", "value": JsonUtil.dumps({}), "desc": "异步回调数据源"},
            {"name": "default_diff_message_send_addr", "value": "", "desc": "yapi接口监控报告默认发送钉钉机器人地址"},
            {"name": "run_time_out", "value": "600", "desc": "前端运行测试时，等待的超时时间，秒"},
            {"name": "report_host", "value": "http://localhost", "desc": "查看报告域名"},
            {"name": "pagination_size", "value": JsonUtil.dumps(pagination_size), "desc": "默认分页信息"},
            {"name": "callback_webhook", "value": "", "desc": "接口收到回调请求后即时通讯通知的地址"},
            {"name": "test_type", "value": JsonUtil.dumps(test_type), "desc": "测试类型"},
            {"name": "call_back_msg_addr", "value": call_back_msg_addr, "desc": "发送回调流水线消息内容地址"},
            {"name": "save_func_permissions", "value": "0", "desc": "保存脚本权限，0所有人都可以，1管理员才可以"},
            {
                "name": "call_back_response",
                "value": "",
                "desc": "回调接口的响应信息，若没有设置值，则回调代码里面的默认响应"
            },
            {
                "name": "func_error_addr",
                "value": "/#/assist/errorRecord",
                "desc": "展示自定义函数错误记录的前端地址（用于即时通讯通知）"
            },
            {
                "name": "make_user_info_mapping",
                "value": JsonUtil.dumps(make_user_info_mapping),
                "desc": "生成用户信息的可选项，映射faker的模块（不了解faker模块勿改）"
            },
            {
                "name": "make_user_language_mapping",
                "value": JsonUtil.dumps(make_user_language_mapping),
                "desc": "生成用户信息的可选语言，映射faker的模块（不了解faker模块勿改）"
            },
        ],

        "接口自动化": [
            {"name": "http_methods", "value": "GET,POST,PUT,DELETE,PATCH,HEAD,OPTIONS",
             "desc": "http请求方式，以英文的 ',' 隔开"},
            {"name": "run_time_error_message_send_addr", "value": "", "desc": "运行测试用例时，有错误信息实时通知地址"},
            {"name": "request_time_out", "value": 60, "desc": "运行测试步骤时，request超时时间"},
            {"name": "api_suite_list", "value": JsonUtil.dumps(api_suite_list), "desc": "接口自动化用例集类型"},
            {
                "name": "response_data_source_mapping",
                "value": JsonUtil.dumps(response_data_source_mapping),
                "desc": "响应对象数据源映射"
            },
            {
                "name": "api_report_addr",
                "value": "/#/apiTest/reportShow?id=",
                "desc": "展示测试报告页面的前端地址（用于即时通讯通知）"
            },
            {
                "name": "diff_api_addr",
                "value": "/#/assist/diffRecordShow?id=",
                "desc": "展示yapi监控报告页面的前端地址（用于即时通讯通知）"
            }
        ],

        "webUi自动化": [
            {"name": "wait_time_out", "value": 10, "desc": "等待元素出现时间"},
            {"name": "browser_name", "value": JsonUtil.dumps(browser_name), "desc": "支持的浏览器"},
            {"name": "ui_suite_list", "value": JsonUtil.dumps(ui_suite_list), "desc": "UI自动化用例集类型"},
            {
                "name": "find_element_option",
                "value": JsonUtil.dumps(find_element_option),
                "desc": "ui自动化定位元素方式"
            },
            {
                "name": "web_ui_report_addr",
                "value": "/#/webUiTest/reportShow?id=",
                "desc": "展示测试报告页面的前端地址（用于即时通讯通知）"
            }
        ],

        "appUi自动化": [
            {"name": "server_os_mapping", "value": JsonUtil.dumps(server_os_mapping), "desc": "appium服务器系统类型"},
            {"name": "phone_os_mapping", "value": JsonUtil.dumps(phone_os_mapping), "desc": "运行app自动化的手机系统"},
            {"name": "app_key_code", "value": JsonUtil.dumps(app_key_code), "desc": "模拟手机键盘输入code"},
            {
                "name": "app_ui_report_addr",
                "value": "/#/appUiTest/reportShow?id=",
                "desc": "展示测试报告页面的前端地址（用于即时通讯通知）"
            }
        ]
    }
    for conf_type, conf_list in conf_dict.items():
        for conf in conf_list:
            if Config.get_first(name=conf["name"]) is None:
                conf["type"] = type_dict[conf_type]
                Config().create(conf)
                print_item_delimiter(f'配置【{conf["name"]}】创建成功')
    print_type_delimiter("配置创建完成")


@manager.command
def init_script():
    """ 初始化脚本文件模板 """
    print_type_delimiter("开始创建函数文件模板")
    func_file_list = [
        {"name": "base_template", "num": 0, "desc": "自定义函数文件使用规范说明"},
        {"name": "utils_template", "num": 1, "desc": "工具类自定义函数操作模板"},
        {"name": "database_template", "num": 2, "desc": "数据库操作类型的自定义函数文件模板"}
    ]
    if Script.get_first() is None:
        for data in func_file_list:
            with open(os.path.join("static", f'{data["name"]}.py'), "r", encoding="utf-8") as fp:
                func_data = fp.read()
            data["script_data"] = func_data
            Script().create(data)
            print_item_delimiter(f'函数文件【{data["name"]}】创建成功')
    print_type_delimiter("函数文件模板创建完成")


@manager.command
def init_run_env():
    """ 初始化运行环境 """
    print_type_delimiter("开始创建运行环境")
    env_dict = [
        {"name": "开发环境", "code": "dev_qa", "desc": "开发环境", "group": "QA环境"},
        {"name": "测试环境", "code": "test_qa", "desc": "测试环境", "group": "QA环境"},
        {"name": "uat环境", "code": "uat_qa", "desc": "uat环境", "group": "QA环境"},
        {"name": "生产环境", "code": "production_qa", "desc": "生产环境", "group": "QA环境"},
    ]
    if RunEnv.get_first() is None:  # 没有运行环境则创建
        for index, env in enumerate(env_dict):
            if RunEnv.get_first(code=env["code"]) is None:
                env["num"] = index
                RunEnv().create(env)
                print_item_delimiter(f'运行环境【{env["name"]}】创建成功')
    print_type_delimiter("运行环境创建完成")


@manager.command
def init():
    """ 初始化 权限、角色、管理员 """
    print_start_delimiter("开始初始化数据")
    init_permission()
    init_role()
    init_user()
    init_config_type()
    init_config()
    init_script()
    init_run_env()
    print_start_delimiter("数据初始化完毕")


"""
初始化数据库
python dbMigration.py db init
python dbMigration.py db migrate
python dbMigration.py db upgrade

初始化数据
python dbMigration.py init
"""

if __name__ == "__main__":
    manager.run()
