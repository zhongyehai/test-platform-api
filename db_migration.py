# -*- coding: utf-8 -*-
import json
import os.path

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from utils.util.json_util import JsonUtil
from app.base_model import db
from app.system.model_factory import User, Permission, Role, RolePermissions, UserRoles
from app.config.model_factory import Config, ConfigType
from app.config.model_factory import RunEnv
from app.config.model_factory import BusinessLine
from app.assist.model_factory import Script
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

device_extends = {
    "contact_count": "联系人个数",
    "contact_person_count": "通讯录条数",
    "note_record_count": "短信条数",
    "app_installed_record_count": "APP安装数量"
}

# 2024 年的节假日，每年需手动更新
holiday_list = [
    "01-01",
    "02-10", "02-11", "02-12", "02-13", "02-14", "02-15", "02-16", "02-17",
    "04-04", "04-05", "04-06",
    "05-01", "05-02", "05-03", "05-04", "05-05",
    "06-08", "06-09", "06-10",
    "09-15", "09-16", "09-17",
    "10-01", "10-02", "10-03", "10-04", "10-05", "10-06", "10-07"
]

# 回调流水线消息内容
call_back_msg_addr = ""

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
                    Permission.model_create(rule)
                    print_type_delimiter(f'权限【{rule["name"]}】创建成功')
    print_type_delimiter("权限创建完成")


@manager.command
def init_role():
    """ 初始化角色和对应的权限 """
    print_type_delimiter("开始创建角色")

    print_type_delimiter("开始创建【后端管理员】角色")
    if Role.get_first(name="管理员-后端") is None:
        admin_role = Role.model_create_and_get({"name": "管理员-后端", "desc": "后端管理员, 有权限访问任何接口"})
        admin_permission = Permission.get_first(source_addr='admin', source_type='api')
        RolePermissions.model_create({"role_id": admin_role.id, "permission_id": admin_permission.id})
    print_type_delimiter("【后端管理员】创建完成")

    print_type_delimiter("开始创建【前端管理员】角色")
    if Role.get_first(name="管理员-前端") is None:
        admin_role = Role.model_create_and_get({"name": "管理员-前端", "desc": "前端管理员, 有权限访问任何页面、按钮"})
        admin_permission = Permission.get_first(source_addr='admin', source_type='front')
        RolePermissions.model_create({"role_id": admin_role.id, "permission_id": admin_permission.id})
    print_type_delimiter("【前端管理员】创建完成")

    print_type_delimiter("开始创建测试人员角色")
    if Role.get_first(name="测试人员") is None:
        test_role = Role.model_create_and_get({"name": "测试人员", "desc": "能访问项目的基本信息，不能访问配置管理"})
        for source_type, permission_rules in permission_dict.items():
            if source_type == "front":
                for rule_type, source_addr_list in permission_rules.items():
                    for source in source_addr_list:
                        addr = source["source_addr"]
                        if addr.startswith(('/system', '/system', '/help', 'admin')) is False:
                            permission = Permission.get_first(source_addr=addr)
                            RolePermissions.model_create({"role_id": test_role.id, "permission_id": permission.id})
    print_type_delimiter("测试人员角色创建完成")

    print_type_delimiter("开始创建业务线负责人角色")
    if Role.get_first(name="业务线负责人") is None:
        test_role = Role.get_first(name="测试人员")
        manager_role = Role.model_create_and_get({
            "name": "业务线负责人",
            "desc": "有权限访问项目的任何页面、按钮和配置管理",
            "extend_role": [test_role.id]
        })
        for source_type, permission_rules in permission_dict.items():
            if source_type == "front":
                for rule_type, source_addr_list in permission_rules.items():
                    for source in source_addr_list:
                        addr = source["source_addr"]
                        # 负责人给配置管理、用户管理权限
                        if addr in ['/system', '/api/system/role/list'] or addr.startswith(
                                ('/config', '/system/user', '/api/system/user')):
                            permission = Permission.get_first(source_addr=addr)
                            RolePermissions.model_create({"role_id": manager_role.id, "permission_id": permission.id})

    print_type_delimiter("业务线负责人角色创建完成")

    print_type_delimiter("角色创建完成")


@manager.command
def init_user():
    """ 初始化用户和对应的角色 """

    # 创建业务线
    print_type_delimiter("开始创建业务线")
    business_dict = {"name": "公共业务线", "code": "common", "desc": "公共业务线，所有人都可见、可操作", "num": 0}
    business = BusinessLine.get_first(code=business_dict["code"])
    if business is None:
        all_env_id_list = [run_env[0] for run_env in RunEnv.db.session.query(RunEnv.id).filter().all()]
        business_dict["env_list"] = all_env_id_list
        business = BusinessLine.model_create_and_get(business_dict)
        print_item_delimiter(f'业务线【{business.name}】创建成功')
    print_type_delimiter("业务线创建完成")

    # 创建用户
    print_type_delimiter("开始创建用户")
    user_list = [
        {"account": "admin", "password": "123456", "name": "管理员", "role": ["管理员-后端", "管理员-前端"]},
        {"account": "manager", "password": "manager", "name": "业务线负责人", "role": ["业务线负责人"]},
        {"account": "common", "password": "common", "name": "测试员", "role": ["测试人员"]}
    ]
    for user_info in user_list:
        if User.get_first(account=user_info["account"]) is None:
            user_role_list = user_info.pop("role")
            user_info["business_list"] = [business.id]
            user = User.model_create_and_get(user_info)
            for role_name in user_role_list:
                role = Role.get_first(name=role_name)
                UserRoles.model_create({"user_id": user.id, "role_id": role.id})
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
            ConfigType.model_create(data)
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
            {"name": "kym", "value": JsonUtil.dumps(kym_keyword), "desc": "KYM分析项"},
            {"name": "sync_mock_data", "value": JsonUtil.dumps({}), "desc": "同步回调数据源"},
            {"name": "async_mock_data", "value": JsonUtil.dumps({}), "desc": "异步回调数据源"},
            {"name": "holiday_list", "value": JsonUtil.dumps(holiday_list), "desc": "节假日/调休日期，需每年手动更新"},
            {"name": "run_time_out", "value": "600", "desc": "前端运行测试时，等待的超时时间，秒"},
            {"name": "report_host", "value": "http://localhost", "desc": "查看报告域名"},
            {"name": "callback_webhook", "value": "", "desc": "接口收到回调请求后即时通讯通知的地址"},
            {"name": "call_back_msg_addr", "value": call_back_msg_addr, "desc": "发送回调流水线消息内容地址"},
            {"name": "save_func_permissions", "value": "0", "desc": "保存脚本权限，0所有人都可以，1管理员才可以"},
            {
                "name": "call_back_response",
                "value": "",
                "desc": "回调接口的响应信息，若没有设置值，则回调代码里面的默认响应"
            },
            {
                "name": "func_error_addr",
                "value": "/assist/errorRecord",
                "desc": "展示自定义函数错误记录的前端地址（用于即时通讯通知）"
            }
        ],

        "接口自动化": [
            {"name": "run_time_error_message_send_addr", "value": "", "desc": "运行测试用例时，有错误信息实时通知地址"},
            {"name": "request_time_out", "value": 60, "desc": "运行测试步骤时，request超时时间"},
            {
                "name": "api_report_addr",
                "value": "/apiTest/reportShow?id=",
                "desc": "展示测试报告页面的前端地址（用于即时通讯通知）"
            },
            {
                "name": "diff_api_addr",
                "value": "/assist/diffRecordShow?id=",
                "desc": "展示yapi监控报告页面的前端地址（用于即时通讯通知）"
            }
        ],

        "webUi自动化": [
            {"name": "wait_time_out", "value": 10, "desc": "等待元素出现时间"},
            {
                "name": "web_ui_report_addr",
                "value": "/webUiTest/reportShow?id=",
                "desc": "展示测试报告页面的前端地址（用于即时通讯通知）"
            }
        ],

        "appUi自动化": [
            {"name": "device_extends", "value": JsonUtil.dumps(device_extends),
             "desc": "创建设备时，默认的设备详细数据"},
            {
                "name": "appium_new_command_timeout",
                "value": 120,
                "desc": "两条appium命令间的最长时间间隔，若超过这个时间，appium会自动结束并退出app，单位为秒"
            },
            {
                "name": "app_ui_report_addr",
                "value": "/appUiTest/reportShow?id=",
                "desc": "展示测试报告页面的前端地址（用于即时通讯通知）"
            }
        ]
    }
    for conf_type, conf_list in conf_dict.items():
        for conf in conf_list:
            if Config.get_first(name=conf["name"]) is None:
                conf["type"] = type_dict[conf_type]
                Config.model_create(conf)
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
            Script.model_create(data)
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
                RunEnv.model_create(env)
                print_item_delimiter(f'运行环境【{env["name"]}】创建成功')
    print_type_delimiter("运行环境创建完成")


@manager.command
def init():
    """ 初始化 权限、角色、管理员 """
    print_start_delimiter("开始初始化数据")
    init_run_env()
    init_permission()
    init_role()
    init_user()
    init_config_type()
    init_config()
    init_script()
    print_start_delimiter("数据初始化完毕")


"""
初始化数据库
python db_migration.py db init
python db_migration.py db migrate
python db_migration.py db upgrade

初始化数据
python db_migration.py init
"""

if __name__ == "__main__":
    manager.run()
