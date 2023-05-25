# -*- coding: utf-8 -*-
import re

import validators
from flask import request, g, abort
from wtforms import Form, ValidationError

from utils.util.jsonUtil import JsonUtil
from utils.client.testRunner.parser import extract_variables, parse_function, extract_functions


class BaseForm(Form, JsonUtil):
    """ 初始化Form校验基类，并初统一处理请求参数 """

    def __init__(self):
        """ 初始化的时候获取所有参数一起传给BaseForm """
        data, args = request.get_json(silent=True) or request.form.to_dict(), request.args.to_dict()
        super(BaseForm, self).__init__(data=data, **args)

    def do_validate(self):
        """ 进行form实例化和校验，校验不通过则抛400异常 """
        if not super(BaseForm, self).validate():
            abort(400, self.get_error())
        return self

    def get_error(self):
        """ 获取form校验不通过的报错 """
        return self.errors.popitem()[1][0]

    def is_admin(self):
        """ 管理员权限 """
        return 'admin' in g.api_permissions

    def is_not_admin(self):
        """ 非管理员 """
        return not self.is_admin()

    def is_can_delete(self, is_manager, obj):
        """
        判断是否有权限删除，
        可删除条件（或）：
        1.当前用户为系统管理员
        2.当前用户为当前数据的创建者
        3.当前用户为当前要删除服务的负责人
        """
        return is_manager or self.is_admin() or obj.is_create_user(g.user_id)

    def set_attr(self, **kwargs):
        """ 根据键值对 对form对应字段的值赋值 """
        for key, value in kwargs.items():
            if hasattr(self, key):
                getattr(self, key).data = value

    def validate_func(self, func_container: dict, content: str, message=""):

        functions = extract_functions(content)

        # 使用了自定义函数，但是没有引用函数文件的情况
        if functions and not func_container:
            raise ValidationError(f"{message}要使用自定义函数则需引用对应的函数文件")

        # 使用了自定义函数，但是引用的函数文件中没有当前函数的情况
        for function in functions:
            func_name = parse_function(function)["func_name"]
            if func_name not in func_container:
                raise ValidationError(f"{message}引用的自定义函数【{func_name}】在引用的函数文件中均未找到")

    def validate_is_regexp(self, regexp):
        """ 校验字符串是否为正则表达式 """
        return re.compile(r".*\(.*\).*").match(regexp)

    def validate_variable(self, variables_container: dict, content: str, message=""):
        """ 引用的变量需存在 """
        for variable in extract_variables(content):
            if variable not in variables_container:
                raise ValidationError(f"{message}引用的变量【{variable}】不存在")

    def validate_header_format(self, content: list):
        """ 头部信息，格式校验 """
        for index, data in enumerate(content):
            title, key, value = f"头部信息设置，第【{index + 1}】行", data.get("key"), data.get("value")
            if not ((key and value) or (not key and not value)):
                raise ValidationError(f"{title}，要设置头部信息，则key和value都需设置")

    def validate_variable_format(self, content: list, msg_title='自定义变量'):
        """ 自定义变量，格式校验 """
        for index, data in enumerate(content):
            title = f"{msg_title}设置，第【{index + 1}】行"
            key, value, data_type = data.get("key"), data.get("value"), data.get("data_type")

            # 校验格式
            # 要设置变量，则key、数据类型、备注必传
            if key or data_type:
                if msg_title == 'form-data':
                    if not key or not data_type:
                        raise ValidationError(f"{title}，要设置{msg_title}，则【key、数据类型、备注】都需设置")
                else:
                    if not key or not data_type or not data.get("remark"):
                        raise ValidationError(f"{title}，要设置{msg_title}，则【key、数据类型、备注】都需设置")

            # 检验数据类型
            if key:
                if self.validate_data_format(value, data_type) is False:
                    raise ValidationError(f"{title}，{msg_title}值与数据类型不匹配")

    def validate_data_format(self, value, data_type):
        """ 校验数据格式 """
        try:
            if data_type in ["variable", "func", "str", "file", "True", "False"]:
                pass
            elif data_type == "json":
                self.dumps(self.loads(value))
            else:  # python数据类型
                eval(f"{data_type}({value})")
        except Exception as error:
            return False

    def validate_api_validates(self, data):
        """ 校验断言信息，全都有才视为有效 """
        for index, validate in enumerate(data):
            row_msg = f"断言，第【{index + 1}】行，"
            data_source, key = validate.get("data_source"), validate.get("key")
            validate_type = validate.get("validate_type")
            data_type, value = validate.get("data_type"), validate.get("value")

            if (not data_source and not data_type) or (
                    data_source and not key and validate_type and data_type and not value):
                continue
            elif (data_source and not data_type) or (not data_source and data_type):
                raise ValidationError(
                    f"{row_msg}若要进行断言，则实际结果数据源和预期结果数据类型需同时存在，若不进行断言，则实际结果数据源和预期结果数据类型需同时不存在"
                )

            else:  # 有效的断言
                # 实际结果，选择的数据源为正则表达式，但是正则表达式错误
                if data_source == "regexp" and not self.validate_is_regexp(key):
                    raise ValidationError(f"{row_msg}正则表达式【{key}】错误")

                if not validate_type:  # 没有选择断言类型
                    raise ValidationError(f"{row_msg}请选择断言类型")

                if value is None:  # 要进行断言，则预期结果必须有值
                    raise ValidationError(f"{row_msg}预期结果需填写")

                self.validate_data_type_(row_msg, data_type, value)  # 校验预期结果的合法性

    def validate_data_type_(self, row, data_type, value):
        """ 校验数据类型 """
        if data_type in ["str", "file"]:  # 普通字符串和文件，不校验
            pass
        elif data_type == "variable":  # 预期结果为自定义变量，能解析出变量即可
            if extract_variables(value).__len__() < 1:
                raise ValidationError(f"{row}引用的变量表达式【{value}】错误")
        elif data_type == "func":  # 预期结果为自定义函数，校验校验预期结果表达式、实际结果表达式
            # self.validate_func(func_container, value, message=row)  # 实际结果表达式是否引用自定义函数
            pass
        elif data_type == "json":  # 预期结果为json
            try:
                self.dumps(self.loads(value))
            except Exception as error:
                raise ValidationError(f"{row}预期结果【{value}】，不可转为【{data_type}】")
        else:  # python数据类型
            try:
                eval(f"{data_type}({value})")
            except Exception as error:
                raise ValidationError(f"{row}预期结果【{value}】，不可转为【{data_type}】")

    def validate_api_extracts(self, data):
        """ 校验接口测试数据提取表达式 """
        for index, validate in enumerate(data):
            row = f"数据提取，第【{index + 1}】行，"
            data_source, key, value = validate.get("data_source"), validate.get("key"), validate.get("value")

            if key or data_source:
                if not key or not data_source or not validate.get("remark"):
                    raise ValidationError(f"数据提取第 {row} 行，要设置数据提取，则【key、数据源、备注】都需设置")

            # 实际结果，选择的数据源为正则表达式，但是正则表达式错误
            if key and data_source == "regexp" and value and not self.validate_is_regexp(value):
                raise ValidationError(f"数据提取第 {row} 行，正则表达式【{value}】错误")

    def validate_ui_extracts(self, data):
        """ 校验ui测试数据提取表达式 """
        for index, validate in enumerate(data):
            row = f"数据提取，第【{index + 1}】行，"
            extract_type, key, value = validate.get("extract_type"), validate.get("key"), validate.get("value")

            if key or extract_type:
                if not key or not extract_type or not validate.get("remark"):
                    raise ValidationError(f"数据提取第 {row} 行，要设置数据提取，则【key、提取方式、备注】都需设置")

    def validate_data_is_exist(self, error_msg, model, **kwargs):
        """ 校验数据已存在，存在则返回数据模型 """
        data = model.get_first(**kwargs)
        if data:
            return data
        raise ValidationError(error_msg)

    def validate_data_is_not_exist(self, error_msg, model, **kwargs):
        """ 校验数据不存在 """
        if model.get_first(**kwargs):
            raise ValidationError(error_msg)

    def validate_data_is_not_repeat(self, error_msg, model, current_data_id, **kwargs):
        """ 校验数据不重复 """
        data = model.get_first(**kwargs)
        if data and data.id != current_data_id:
            raise ValidationError(error_msg)

    def validate_data_is_true(self, error_msg, data):
        """ 校验数据为真 """
        if not data:
            raise ValidationError(error_msg)

    def validate_data_is_false(self, error_msg, data):
        """ 校验数据为假 """
        if data:
            raise ValidationError(error_msg)

    def validate_call_back(self, field):
        """ 校验回调信息 """
        if field.data:
            try:
                if isinstance(field.data, list) is False:
                    raise
            except Exception as error:
                raise ValidationError("回调信息错误，若需要回调，请按示例填写")

    def validate_skip_if(self, field):
        """ 校验跳过条件 """
        if hasattr(self, "quote_case"):
            if self.quote_case.data:
                return
        for index, skip_if in enumerate(field.data):
            index += 1
            skip_type, data_source = skip_if.get("skip_type"), skip_if.get("data_source")
            check_value, comparator = skip_if.get("check_value"), skip_if.get("comparator")
            data_type, expect = skip_if.get("data_type"), skip_if.get("expect")
            if any((skip_type, data_source, check_value, comparator, data_type, expect)):
                if data_source not in ["run_env", "run_server", "run_device"]:  # 常规数据校验
                    if all((skip_type, data_source, check_value, comparator, data_type, expect)) is False:
                        raise ValidationError(f"【跳过条件】第【{index}】行设置的条件错误，请检查")
                    try:
                        if data_type in ["variable", "func", "str"]:
                            continue
                        elif data_type == "json":
                            self.dumps(self.loads(expect))
                            continue
                        else:  # python数据类型
                            eval(f"{data_type}({expect})")
                            continue
                    except Exception as error:
                        raise ValidationError(f"【跳过条件】第【{index}】行设置的条件错误，请检查")
                else:  # 运行环境、运行服务器、运行终端
                    if all((skip_type, data_source, comparator, expect)) is False:
                        raise ValidationError(f"【跳过条件】第【{index}】行设置的条件错误，请检查")

    def validate_email(self, email_server, email_from, email_pwd, email_to):
        """ 发件邮箱、发件人、收件人、密码 """
        if not email_server:
            raise ValidationError("选择了要邮件接收，则发件邮箱服务器必填")

        if not email_to or not email_from or not email_pwd:
            raise ValidationError("选择了要邮件接收，则发件人、收件人、密码3个必须有值")

        # 校验发件邮箱
        if email_from and not validators.email(email_from.strip()):
            raise ValidationError(f"发件人邮箱【{email_from}】格式错误")

        # 校验收件邮箱
        for mail in email_to:
            mail = mail.strip()
            if mail and not validators.email(mail):
                raise ValidationError(f"收件人邮箱【{mail}】格式错误")
