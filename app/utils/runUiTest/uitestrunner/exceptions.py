# encoding: utf-8

from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import *

from .compat import JSONDecodeError, FileNotFoundError

""" 失败类型的异常，这些异常会将测试标记为失败 """


class MyBaseFailure(Exception):
    pass


class ValidationFailure(MyBaseFailure):
    pass


class ExtractFailure(MyBaseFailure):
    pass


class SetupHooksFailure(MyBaseFailure):
    pass


class TeardownHooksFailure(MyBaseFailure):
    pass


""" 错误类型异常，这些异常将把测试标记为错误 """


class MyBaseError(Exception):
    pass


class FileFormatError(MyBaseError):
    pass


class ParamsError(MyBaseError):
    pass


class NotFoundError(MyBaseError):
    pass


class FileNotFound(FileNotFoundError, NotFoundError):
    pass


class FunctionNotFound(NotFoundError):
    pass


class VariableNotFound(NotFoundError):
    pass


class EnvNotFound(NotFoundError):
    pass


class CSVNotFound(NotFoundError):
    pass


class ApiNotFound(NotFoundError):
    pass


class TestcaseNotFound(NotFoundError):
    pass


class BrowserDriverNotFound(WebDriverException):
    """ 浏览器驱动没有找到 """

    def __init__(self, msg):
        WebDriverException.__init__(self, msg)


class UITestRunnerTimeoutException(MyBaseError, TimeoutException):
    """ 等待超时 """

    def __init__(self, msg):
        WebDriverException.__init__(self, msg)


class RunTimeException(MyBaseError):
    """ 抛出运行时异常 """

    def __init__(self, msg):
        MyBaseError.__init__(self, msg)
