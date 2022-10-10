# -*- coding: utf-8 -*-
import os.path
from collections import OrderedDict

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from utils.jsonUtil import JsonUtil
from app.baseModel import db
from app.system.models.user import User, Permission, Role
from app.config.models.config import Config, ConfigType
from app.assist.models.func import Func
from main import app

manager = Manager(app)

Migrate(app, db)
manager.add_command('db', MigrateCommand)


def print_start_delimiter(content):
    print(f'{"*" * 20} {content} {"*" * 20}')


def print_type_delimiter(content):
    print(f'    {"=" * 16} {content} {"=" * 16}')


def print_item_delimiter(content):
    print(f'        {"=" * 12} {content} {"=" * 12}')


def print_detail_delimiter(content):
    print(f'            {"=" * 8} {content} {"=" * 8}')


make_user_info_mapping = {
    "姓名": "name",
    "身份证号": "ssn",
    "手机号": "phone_number",
    "银行卡": "credit_card_number",
    "地址": "address",
    "公司名": "company",
    "统一社会信用代码": "credit_code",
    "邮箱": "company_email",
    "工作": "job",
    "ipv4": "ipv4",
    "ipv6": "ipv6"
}

kym_keword = [
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
    {"label": "自定义函数", "value": "func"},
    {"label": "自定义变量", "value": "variable"},
]

# ui自动化元素定位方式
find_element_option = [
    {"label": "根据id属性定位", "value": "id"},
    {"label": "根据xpath表达式定位", "value": "xpath"},
    {"label": "根据class选择器定位", "value": "class name"},
    {"label": "根据css选择器定位", "value": "css selector"},
    {"label": "根据name属性定位", "value": "name"},
    {"label": "根据tag名字定位 ", "value": "tag name"},
    {"label": "根据超链接文本定位", "value": "link text"},
    {"label": "页面地址", "value": "url"}
]

# 环境配置，可根据实际需求自行修改，但环境不可重复
env_dict = {"dev": "开发环境", "test": "测试环境", "uat": "uat环境", "production": "生产环境"}


@manager.command
def init_role():
    """ 初始化权限、角色 """
    print_type_delimiter("开始创建角色")
    roles_permissions_map = OrderedDict()
    roles_permissions_map[u'测试人员'] = ['COMMON']
    roles_permissions_map[u'管理员'] = ['COMMON', 'ADMINISTER']
    for role_name in roles_permissions_map:
        role = Role.get_first(name=role_name)
        if role is None:
            role = Role(name=role_name)
            db.session.add(role)
            role.permission = []
        for permission_name in roles_permissions_map[role_name]:
            permission = Permission.get_first(name=permission_name)
            if permission is None:
                permission = Permission(name=permission_name)
                db.session.add(permission)
            role.permission.append(permission)
            db.session.commit()
    print_type_delimiter("角色创建成功")


@manager.command
def init_user():
    """ 初始化用户 """
    print_type_delimiter("开始创建用户")
    user_list = [
        {'account': 'admin', 'password': '123456', 'name': '管理员', 'status': 1, 'role_id': 2},
        {'account': 'common', 'password': 'common', 'name': '公用账号', 'status': 1, 'role_id': 1}
    ]
    for user_info in user_list:
        if User.get_first(account=user_info['account']) is None:
            User().create(user_info)
            print_item_delimiter(f'用户【{user_info["name"]}】创建成功')
    print_type_delimiter("用户创建完成")


@manager.command
def init_config_type():
    """ 初始化配置类型 """
    print_type_delimiter("开始创建配置类型")
    config_type_list = [
        {'name': '系统配置', 'desc': '全局配置'},
        {'name': '邮箱', 'desc': '邮箱服务器'},
        {'name': '接口自动化', 'desc': '接口自动化测试'},
        {'name': 'ui自动化', 'desc': 'ui自动化测试'}
    ]
    for data in config_type_list:
        if ConfigType.get_first(name=data["name"]) is None:
            ConfigType().create(data)
            print_item_delimiter(f'配置类型【{data["name"]}】创建成功')
    print_type_delimiter("配置类型创建完成")


@manager.command
def init_config():
    """ 初始化配置 """

    type_dict = {config_type.name: config_type.id for config_type in ConfigType.get_all()}  # 所有配置类型
    print_type_delimiter("开始创建配置")
    conf_dict = {
        '邮箱': [
            {'name': 'QQ邮箱', 'value': 'smtp.qq.com', 'desc': 'QQ邮箱服务器'}
        ],

        '系统配置': [
            {'name': 'platform_name', 'value': '极测平台', 'desc': '测试平台名字'},
            {'name': 'run_test_env', 'value': JsonUtil.dumps(env_dict), 'desc': '测试平台支持的环境'},
            {'name': 'make_user_info_mapping', 'value': JsonUtil.dumps(make_user_info_mapping),
             'desc': '生成用户信息的可选项，映射faker的模块（不了解faker模块勿改）'},
            {'name': 'data_type_mapping', 'value': JsonUtil.dumps(data_type_mapping), 'desc': 'python数据类型映射'},
            {'name': 'yapi_host', 'value': '', 'desc': 'yapi域名'},
            {'name': 'yapi_account', 'value': '', 'desc': 'yapi账号'},
            {'name': 'yapi_password', 'value': '', 'desc': 'yapi密码'},
            {'name': 'ignore_keyword_for_group', 'value': '[]', 'desc': '不需要从yapi同步的分组关键字'},
            {'name': 'ignore_keyword_for_project', 'value': '[]', 'desc': '不需要从yapi同步的服务关键字'},
            {'name': 'kym', 'value': JsonUtil.dumps(kym_keword), 'desc': 'KYM分析项'},
            {'name': 'default_diff_message_send_addr', 'value': '', 'desc': 'yapi接口监控报告默认发送钉钉机器人地址'},
            {'name': 'run_time_out', 'value': '60', 'desc': '前端运行测试时，等待的超时时间，秒'},
            {'name': 'call_back_response', 'value': '', 'desc': '回调接口的响应信息，若没有设置值，则回调代码里面的默认响应'},
            {'name': 'callback_webhook', 'value': '', 'desc': '接口收到回调请求后即时通讯通知的地址'},
            {'name': 'func_error_addr', 'value': 'http://localhost/#/assist/errorRecord',
             'desc': '展示自定义函数错误记录的前端地址（用于即时通讯通知）'}
        ],

        '接口自动化': [
            {'name': 'http_methods', 'value': 'GET,POST,PUT,DELETE', 'desc': 'http请求方式，以英文的 "," 隔开'},
            {'name': 'response_data_source_mapping', 'value': JsonUtil.dumps(response_data_source_mapping),
             'desc': '响应对象数据源映射'},
            {'name': 'run_time_error_message_send_addr', 'value': '', 'desc': '运行测试用例时，有错误信息实时通知地址'},
            {'name': 'request_time_out', 'value': 60, 'desc': '运行测试步骤时，request超时时间'},
            {'name': 'is_parse_headers_by_swagger', 'value': "1", 'desc': '从swagger拉取数据时，是否解析头部参数, 1为要同步'},
            {'name': 'api_report_addr', 'value': 'http://localhost/#/apiTest/reportShow?id=',
             'desc': '展示测试报告页面的前端地址（用于即时通讯通知）'},
            {'name': 'diff_api_addr', 'value': 'http://localhost/#/assist/diffRecordShow?id=',
             'desc': '展示yapi监控报告页面的前端地址（用于即时通讯通知）'}
        ],

        'ui自动化': [
            {'name': 'find_element_option', 'value': JsonUtil.dumps(find_element_option), 'desc': 'ui自动化定位元素方式'},
            {'name': 'wait_time_out', 'value': 10, 'desc': '等待元素出现时间'},
            {'name': 'ui_report_addr', 'value': 'http://localhost/#/webUiTest/reportShow?id=',
             'desc': '展示测试报告页面的前端地址（用于即时通讯通知）'}
        ]
    }
    for conf_type, conf_list in conf_dict.items():
        for conf in conf_list:
            if Config.get_first(name=conf["name"]) is None:
                conf['type'] = type_dict[conf_type]
                Config().create(conf)
                print_item_delimiter(f'配置【{conf["name"]}】创建成功')
    print_type_delimiter("配置创建完成")


@manager.command
def init_func_files():
    """ 初始化函数文件模板 """
    print_type_delimiter("开始创建函数文件模板")
    func_file_list = [
        {'name': 'base_template', 'desc': '自定义函数文件使用规范说明'},
        {'name': 'utils_template', 'desc': '工具类自定义函数操作模板'},
        {'name': 'database_template', 'desc': '数据库操作类型的自定义函数文件模板'}
    ]
    for data in func_file_list:
        if Func.get_first(name=data["name"]) is None:
            with open(os.path.join('static', f'{data["name"]}.py'), 'r', encoding='utf-8') as fp:
                func_data = fp.read()
            data["func_data"] = func_data
            Func().create(data)
            print_item_delimiter(f'函数文件【{data["name"]}】创建成功')
    print_type_delimiter("函数文件模板创建完成")


@manager.command
def init():
    """ 初始化 权限、角色、管理员 """
    print_start_delimiter("开始初始化数据")
    init_role()
    init_user()
    init_config_type()
    init_config()
    init_func_files()
    print_start_delimiter("数据初始化完毕")


"""
初始化数据库
python dbMigration.py db init
python dbMigration.py db migrate
python dbMigration.py db upgrade

初始化数据
python dbMigration.py init
"""

if __name__ == '__main__':
    manager.run()
