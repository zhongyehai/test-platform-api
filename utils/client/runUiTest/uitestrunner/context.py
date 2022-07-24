import json

from . import exceptions, logger, parser, utils


class SessionContext(object):
    """ HttpRunner session, store runtime variables.

    Examples:
        >>> functions={...}
        >>> variables = {"SECRET_KEY": "DebugTalk"}
        >>> context = SessionContext(functions, variables)

        Equivalent to:
        >>> context = SessionContext(functions)
        >>> context.update_session_variables(variables)

    """
    def __init__(self, functions, variables=None):
        self.session_variables_mapping = utils.ensure_mapping_format(variables or {})
        self.FUNCTIONS_MAPPING = functions
        self.init_test_variables()
        self.validation_results = []

    def init_test_variables(self, variables_mapping=None):
        """ 初始化测试变量，在每个测试（api）开始时调用。变量映射将首先进行评估。

        Args:
            variables_mapping (dict)
                {
                    "random": "${gen_random_string(5)}",
                    "authorization": "${gen_md5($TOKEN, $data, $random)}",
                    "data": '{"name": "user", "password": "123456"}',
                    "TOKEN": "debugtalk",
                }

        """
        variables_mapping = variables_mapping or {}
        variables_mapping = utils.ensure_mapping_format(variables_mapping)

        self.test_variables_mapping = {}
        # priority: extracted variable > teststep variable
        self.test_variables_mapping.update(variables_mapping)
        self.test_variables_mapping.update(self.session_variables_mapping)

        for variable_name, variable_value in variables_mapping.items():
            variable_value = self.eval_content(variable_value)
            self.update_test_variables(variable_name, variable_value)

    def update_test_variables(self, variable_name, variable_value):
        """ update test variables, these variables are only valid in the current test.
        """
        self.test_variables_mapping.setdefault(variable_name, variable_value)
        # self.test_variables_mapping[variable_name] = variable_value

    def update_session_variables(self, variables_mapping):
        """ 使用提取的变量映射更新会话。这些变量在整个运行会话中有效。"""
        variables_mapping = utils.ensure_mapping_format(variables_mapping)
        self.session_variables_mapping.update(variables_mapping)
        self.test_variables_mapping.update(self.session_variables_mapping)

    def eval_content(self, content):
        """ 递归解析内容中的每个变量和函数。内容可以是任何数据结构，包括字典、列表、元组、数字、字符串等。"""
        return parser.parse_data(
            content,
            self.test_variables_mapping,
            self.FUNCTIONS_MAPPING
        )

    def __eval_check_item(self, validator):
        """ evaluate check item in validator.

        Args:
            validator (dict): validator
                {"check": "status_code", "comparator": "eq", "expect": 201}
                {"check": "$resp_body_success", "comparator": "eq", "expect": True}
            resp_obj (object): requests.Response() object

        Returns:
            dict: validator info
                {
                    "check": "status_code",
                    "check_value": 200,
                    "expect": 201,
                    "comparator": "eq"
                }

        """
        validator["check_value"] = self.eval_content(validator["check"])
        validator["expect"] = self.eval_content(validator["expect"])
        validator["check_result"] = "unchecked"
        return validator

    def _do_validation(self, validator_dict, driver):
        """ 执行断言

        Args:
            validator_dict (dict): validator dict
                {
                    "comparator": "assert_56text_in_value",
                    "check": ('id', 'kw'),
                    "expect": "123123",
                    "check_value": ['id', 'kw'],
                    "check_result": "unchecked"
                }
        """
        validate_func = getattr(driver, validator_dict["comparator"])

        check_element = validator_dict["check"]
        check_value = validator_dict["check_value"]
        expect_value = validator_dict["expect"]
        check_value_type, expect_value_type = type(check_value).__name__, type(expect_value).__name__

        try:
            validator_dict["check_result"] = "pass"
            validate_func(check_element, expect_value)
            logger.log_debug(f"断言: "
                             f"{check_element} "
                             f"{validate_func.__doc__} "
                             f"{expect_value}({type(expect_value).__name__}) "
                             f"==> pass")
        except (AssertionError, TypeError) as error:
            print(f'error: {error}')
            # print(f'str(error): {str(error)}')
            # print(f'str(error): {str(error)}')
            # error = json.loads(str(error))
            # 方便在页面上对比，转为dict
            try:
                if isinstance(expect_value, str):
                    expect_value = json.loads(expect_value)
            except Exception as json_loads_error:
                pass

            error_msg = f"""
            断言不通过\n
            断言方式: {validate_func.__doc__}\n
            预期结果: {expect_value}({expect_value_type})\n
            实际结果定位元素: {check_value}\n
            实际结果: {error}\n
            描述：{error}
            """
            # 实际结果: {error.get('expect_value') or error.get('msg')}\n
            # 断言结果: {error}  # 断言未通过，断言方式为相等
            validator_dict["check_result"] = "fail"
            raise exceptions.ValidationFailure(error_msg)

    def validate(self, validators, driver):
        """ 执行断言 """
        self.validation_results = []
        if not validators:
            return

        logger.log_debug("开始断言")

        validate_pass = True
        failures = []

        for validator in validators:

            evaluated_validator = self.__eval_check_item(parser.parse_validator(validator))
            try:
                self._do_validation(evaluated_validator, driver)
            except exceptions.ValidationFailure as ex:
                validate_pass = False
                failures.append(str(ex))

            self.validation_results.append(evaluated_validator)

        if not validate_pass:  # 断言未通过
            failures_string = "\n".join([failure for failure in failures])
            raise exceptions.ValidationFailure(failures_string)
