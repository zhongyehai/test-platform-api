import json
import re
from typing import Optional, Union

import requests
import validators
from pydantic import BaseModel as pydanticBaseModel, Field
from flask import request, g

from utils.util.json_util import JsonUtil
from utils.client.test_runner.parser import extract_variables, parse_function, extract_functions


def required_str_field(*args, **kwargs):
    """ 必传字段, 且长度大于1，防止传null、空字符串 """
    kwargs["min_length"] = 1
    return Field(..., **kwargs)


class ParamModel(pydanticBaseModel):
    key: Union[str, None] = None
    value: Union[str, None] = None


class HeaderModel(ParamModel):
    remark: Union[str, None] = None


class DataFormModel(HeaderModel):
    data_type: Union[str, None] = None


class VariablesModel(DataFormModel):
    pass


class ExtractModel(HeaderModel):
    value: Optional[Union[str, int, None]] = None
    status: Union[int, None] = None
    data_source: Union[str, None] = None
    extract_type: Union[str, None] = None
    update_to_header: Optional[Union[str, bool, int, None]] = None


class ValidateModel(HeaderModel):
    status: Union[str, int, None] = None
    validate_type: Union[str, int, None] = None
    data_type: Union[str, int, None] = None
    data_source: Union[str, int, None] = None
    validate_method: Union[str, int, None] = None


class SkipIfModel(HeaderModel):
    expect: Union[str, None] = None
    data_type: Union[str, None] = None
    skip_type: Union[str, None] = None
    comparator: Union[str, None] = None
    check_value: Union[str, None] = None
    data_source: Union[str, None] = None


class AddCaseDataForm(pydanticBaseModel):
    name: str = required_str_field(title="名字")
    desc: str = required_str_field(title="描述")


class AddElementDataForm(pydanticBaseModel):
    name: str = required_str_field(title="名字")
    by: str = required_str_field(title="定位方式")
    element: str = required_str_field(title="定位表达式")
    template_device: Optional[int] = Field(None, title="定位元素时参照的手机")


class AddEnvDataForm(pydanticBaseModel):
    name: Optional[str] = Field(None, title="域名")
    value: Optional[str] = Field(None, title="域名值")
    desc: Optional[str] = Field(None, title="描述")


class AddEnvAccountDataForm(pydanticBaseModel):
    name: Optional[str] = Field(None, title="名字")
    value: Optional[str] = Field(None, title="值")
    password: Optional[str] = Field(None, title="密码")
    desc: Optional[str] = Field(None, title="描述")


# class AddUiElementDataForm(pydanticBaseModel):
#     name: str = required_str_field(title="名字")
#     by: str = required_str_field(title="定位方式")
#     element: str = required_str_field(title="定位表达式")


class BaseForm(pydanticBaseModel, JsonUtil):
    """ 基类数据模型 """

    def __init__(self):
        """ 实例化的时候获取所有参数一起传给BaseForm，pydantic会在实例化的时候自动进行数据校验 """
        g.current_from = self  # 初始胡的时候把form放g上，方便在处理异常的时候获取字段title，提示用户
        request_data = request.get_json(silent=True) or request.form.to_dict() or request.args.to_dict()
        super(BaseForm, self).__init__(**request_data)

    @classmethod
    def get_filed_title(cls, filed):
        """ 获取字段的title """
        filed_obj = cls.model_fields.get(filed)  # 嵌套的模型，可能拿不到具体字段
        return filed_obj.title if filed_obj else filed

    @classmethod
    def validate_data_is_exist(cls, msg: str, db_model, **kwargs):
        """ 校验数据是否存在 """
        db_data = db_model.get_first(**kwargs)
        if db_data is None:
            raise ValueError(msg or f"数据不存在")
        return db_data

    @classmethod
    def validate_data_is_not_exist(cls, msg: str, db_model, **kwargs):
        """ 校验数据不存在 """
        if db_model.get_first(**kwargs):
            raise ValueError(msg)

    @classmethod
    def validate_data_is_not_repeat(cls, msg: str, db_model, data_id, **kwargs):
        """ 校验数据是否重复 """
        db_data = db_model.get_first(**kwargs)
        if db_data and db_data.id != data_id:
            raise ValueError(msg)
        return db_data

    @classmethod
    def validate_is_true(cls, data, msg):
        """ 判断为真 """
        if not data:
            raise ValueError(msg)

    @classmethod
    def validate_is_false(cls, data, msg):
        """ 判断为假 """
        if data:
            raise ValueError(msg)

    @classmethod
    def validate_email(cls, email_server, email_from, email_pwd, email_to):
        """ 发件邮箱、发件人、收件人、密码 """
        if not email_server:
            raise ValueError("选择了要邮件接收，则发件邮箱服务器必填")

        if not email_to or not email_from or not email_pwd:
            raise ValueError("选择了要邮件接收，则发件人、收件人、密码3个必须有值")

        # 校验发件邮箱
        if email_from and not validators.email(email_from.strip()):
            raise ValueError(f"发件人邮箱【{email_from}】格式错误")

        # 校验收件邮箱
        for mail in email_to:
            mail = mail.strip()
            if mail and not validators.email(mail):
                raise ValueError(f"收件人邮箱【{mail}】格式错误")

    @classmethod
    def validate_func(cls, func_container: dict, content: str, message=""):

        functions = extract_functions(content)

        # 使用了自定义函数，但是没有引用函数文件的情况
        if functions and not func_container:
            raise ValueError(f"{message}要使用自定义函数则需引用对应的函数文件")

        # 使用了自定义函数，但是引用的函数文件中没有当前函数的情况
        for function in functions:
            func_name = parse_function(function)["func_name"]
            if func_name not in func_container:
                raise ValueError(f"{message}引用的自定义函数【{func_name}】在引用的函数文件中均未找到")

    @classmethod
    def validate_is_regexp(cls, regexp):
        """ 校验字符串是否为正则表达式 """
        return re.compile(r".*\(.*\).*").match(regexp)

    def validate_variable(self, variables_container: dict, content: str, message=""):
        """ 引用的变量需存在 """
        for variable in extract_variables(content):
            if variable not in variables_container:
                raise ValueError(f"{message}引用的变量【{variable}】不存在")

    @classmethod
    def validate_header_format(cls, content: list, content_title='头部信息'):
        """ 头部信息，格式校验 """
        for index, data in enumerate(content):
            title, key, value = f"{content_title}设置，第【{index + 1}】行", data.get("key"), data.get("value")
            if not ((key and value) or (not key and not value)):
                raise ValueError(f"{title}，要设置参数，则key和value都需设置")

    @classmethod
    def validate_variable_format(cls, content: list, msg_title='自定义变量'):
        """ 自定义变量，格式校验 """
        for index, data in enumerate(content):
            title = f"{msg_title}设置，第【{index + 1}】行"
            key, value, data_type = data.get("key"), data.get("value"), data.get("data_type")

            # 检验数据类型
            if key:
                if not data_type or not value or not data.get("remark"):
                    raise ValueError(f"{title}，要设置{msg_title}，则【key、数据类型、备注】都需设置")

                if cls.validate_data_format(value, data_type) is False:
                    raise ValueError(f"{title}，{msg_title}值与数据类型不匹配")

    @classmethod
    def validate_data_format(cls, value, data_type):
        """ 校验数据格式 """
        try:
            if data_type in ["variable", "func", "str", "file", "True", "False"]:
                pass
            elif data_type == "json":
                cls.dumps(cls.loads(value))
            else:  # python数据类型
                eval(f"{data_type}({value})")
        except Exception as error:
            return False

    @classmethod
    def validate_data_validates(cls, validate_data, row_msg):
        """ 校验断言信息，全都有才视为有效 """
        data_source, key = validate_data.get("data_source"), validate_data.get("key")
        validate_method = validate_data.get("validate_method")
        data_type, value = validate_data.get("data_type"), validate_data.get("value")

        if (not data_source and not data_type) or (
                data_source and not key and validate_method and data_type and not value):
            return
        elif (data_source and not data_type) or (not data_source and data_type):
            raise ValueError(f"{row_msg}若要进行断言，则数据源、预期结果、数据类型需同时存在")

        else:  # 有效的断言
            # 实际结果，选择的数据源为正则表达式，但是正则表达式错误
            if data_source == "regexp" and not cls.validate_is_regexp(key):
                raise ValueError(f"{row_msg}正则表达式【{key}】错误")

            if not validate_method:  # 没有选择断言方法
                raise ValueError(f"{row_msg}请选择断言方法")

            if value is None:  # 要进行断言，则预期结果必须有值
                raise ValueError(f"{row_msg}预期结果需填写")

            cls.validate_data_type_(row_msg, data_type, value)  # 校验预期结果的合法性

    @classmethod
    def validate_page_validates(cls, validate_data, row_msg):
        validate_method, data_source = validate_data.get("validate_method"), validate_data.get("data_source")
        data_type, value = validate_data.get("data_type"), validate_data.get("value")

        if validate_method and data_source and data_type and value:  # 都存在
            cls.validate_data_type_(row_msg, data_type, value)  # 校验预期结果
        elif validate_method and not data_source and data_type and not value:  # 仅断言方式和数据类型存在
            return
        elif not validate_method and not data_source and not data_type and not value:  # 所有数据都不存在
            return
        else:
            raise ValueError(f"{row_msg}，数据异常，请检查")

    @classmethod
    def validate_base_validates(cls, data):
        """ 校验断言信息，全都有才视为有效 """
        for index, validate_data in enumerate(data):
            if validate_data.get("status") == 1:
                row_msg = f"断言，第【{index + 1}】行，"
                validate_type = validate_data.get("validate_type")

                if not validate_type:  # 没有选择断言类型
                    raise ValueError(f"{row_msg}请选择断言类型")

                if validate_type == 'data':  # 数据断言
                    cls.validate_data_validates(validate_data, row_msg)
                else:  # 页面断言
                    cls.validate_page_validates(validate_data, row_msg)

    @classmethod
    def validate_data_type_(cls, row, data_type, value):
        """ 校验数据类型 """
        if data_type in ["str", "file"]:  # 普通字符串和文件，不校验
            pass
        elif data_type == "variable":  # 预期结果为自定义变量，能解析出变量即可
            if extract_variables(value).__len__() < 1:
                raise ValueError(f"{row}引用的变量表达式【{value}】错误")
        elif data_type == "func":  # 预期结果为自定义函数，校验校验预期结果表达式、实际结果表达式
            # self.validate_func(func_container, value, message=row)  # 实际结果表达式是否引用自定义函数
            pass
        elif data_type == "json":  # 预期结果为json
            try:
                json.dumps(json.loads(value))
            except Exception as error:
                raise ValueError(f"{row}预期结果【{value}】，不可转为【{data_type}】")
        else:  # python数据类型
            try:
                eval(f"{data_type}({value})")
            except Exception as error:
                raise ValueError(f"{row}预期结果【{value}】，不可转为【{data_type}】")

    @classmethod
    def validate_api_extracts(cls, data):
        """ 校验接口测试数据提取表达式 """
        for index, validate in enumerate(data):
            if validate.get("status") == 1:
                row = f"数据提取，第【{index + 1}】"
                data_source, key, value = validate.get("data_source"), validate.get("key"), validate.get("value")

                if key or data_source:
                    if not key or not data_source or not validate.get("remark"):
                        raise ValueError(f"数据提取第 {row} 行，要设置数据提取，则【key、数据源、备注】都需设置")

                # 实际结果，选择的数据源为正则表达式，但是正则表达式错误
                if key and data_source == "regexp" and value and not cls.validate_is_regexp(value):
                    raise ValueError(f"数据提取第 {row} 行，正则表达式【{value}】错误")

    @classmethod
    def validate_ui_extracts(cls, data):
        """ 校验ui测试数据提取表达式 """
        for index, validate in enumerate(data):
            if validate.get("status") == 1:
                row_msg = f"数据提取，第【{index + 1}】行，"
                extract_type, key, value = validate.get("extract_type"), validate.get("key"), validate.get("value")

                if key or extract_type:
                    if not key or not extract_type or not validate.get("remark"):
                        raise ValueError(f"{row_msg}要设置数据提取，则【key、提取方式、备注】都需设置")

    @classmethod
    def validate_appium_server_is_running(cls, server_ip, server_port):
        """ 校验appium服务器是否能访问 """
        try:
            res = requests.get(f'http://{server_ip}:{server_port}', timeout=5)
            if res.status_code >= 500:
                raise
        except Exception as error:
            raise ValueError("设置的appium服务器地址不能访问，请检查")


class ChangeSortForm(BaseForm):
    """ 权限排序校验 """
    id_list: list = required_str_field(title="要排序的id列表")
    page_num: int = Field(1, title="页数")
    page_size: int = Field(99999, title="页码")


class PaginationForm(BaseForm):
    """ 分页的模型 """
    page_num: Optional[int] = Field(None, title="页数")
    page_size: Optional[int] = Field(None, title="页码")
    detail: bool = Field(False, title='是否获取详细数据')

    def get_query_filter(self, *args, **kwargs):
        """ 解析分页条件，此方法需重载 """
        return []
