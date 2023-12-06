from enum import Enum


class BaseEnum(Enum):

    @classmethod
    def get_value_tuple(cls):
        return (filed.value for filed in cls)


class AuthType(str, BaseEnum):
    """ 身份验证类型 """
    login = "login"
    permission = "permission"
    admin = "admin"
    not_auth = "not_auth"


class QueueTypeEnum(str, BaseEnum):
    """ 消息队列类型 """
    rocket_mq = "rocket_mq"
    redis = "redis"


class DataStatusEnum(int, BaseEnum):
    """ 数据状态，启用/禁用 """
    ENABLE = 1
    DISABLE = 0


class ApiLevelEnum(str, BaseEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class ApiMethodEnum(str, BaseEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    PATCH = "PATCH"


class ApiBodyTypeEnum(str, BaseEnum):
    json = "json"
    form = "form"
    text = "text"
    urlencoded = "urlencoded"


class CaseStatusEnum(int, BaseEnum):
    """ 测试用例状态 """
    NOT_DEBUG_AND_NOT_RUN = 0  # 未调试-不执行
    DEBUG_PASS_AND_RUN = 1  # 调试通过-要执行
    DEBUG_PASS_AND_NOT_RUN = 2  # 调试通过-不执行
    NOT_DEBUG_PASS_AND_NOT_RUN = 3  # 调试不通过-不执行


class UiCaseSuiteTypeEnum(str, BaseEnum):
    """ 用例集类型 """
    BASE = "base"  # 基础用例集
    QUOTE = "quote"  # 引用用例集
    PROCESS = "process"  # 流程用例集
    MAKE_DATA = "make_data"  # 造数据用例集


class ApiCaseSuiteTypeEnum(str, BaseEnum):
    """ 用例集类型 """
    api = "api"  # 单接口用例集
    base = "base"  # 基础用例集
    quote = "quote"  # 引用用例集
    process = "process"  # 流程用例集
    make_data = "make_data"  # 造数据用例集


class ReceiveTypeEnum(str, BaseEnum):
    """ 接收通知方式 """
    not_receive = "not_receive"  # 不接收
    ding_ding = "ding_ding"  # 不接收
    we_chat = "we_chat"  # 不接收
    email = "email"  # 不接收


class SendReportTypeEnum(str, BaseEnum):
    """ 发送报告方式 """
    not_send = "not_send"  # 不发送
    always = "always"  # 始终发送
    on_fail = "on_fail"  # 仅用例不通过时发送


class BusinessLineBindEnvTypeEnum(str, BaseEnum):
    """  业务线绑定环境机制 """
    AUTO = "auto"  # 新增环境时自动绑定
    HUMAN = "human"  # 新增环境后手动绑定


class TriggerTypeEnum(str, BaseEnum):
    """ 触发测试的方式 """
    none = ""  # 空
    pipeline = "pipeline"  # 流水线
    page = "page"  # 页面
    cron = "cron"  # 定时任务
