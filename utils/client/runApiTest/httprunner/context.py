import json

from . import exceptions, logger, parser, utils, built_in


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

    def __eval_check_item(self, validator, resp_obj):
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
        check_item = validator["check"]
        # check_item should only be the following 5 formats:
        # 1, variable reference, e.g. $token
        # 2, function reference, e.g. ${is_status_code_200($status_code)}
        # 3, dict or list, maybe containing variable/function reference, e.g. {"var": "$abc"}
        # 4, string joined by delimiter. e.g. "status_code", "headers.content-type"
        # 5, regex string, e.g. "LB[\d]*(.*)RB[\d]*"

        if isinstance(check_item, (dict, list)) \
            or parser.extract_variables(check_item) \
            or parser.extract_functions(check_item):
            # format 1/2/3
            check_value = self.eval_content(check_item)
        else:
            # format 4/5
            check_value = resp_obj.extract_field(check_item)

        validator["check_value"] = check_value

        # expect_value should only be in 2 types:
        # 1, variable reference, e.g. $expect_status_code
        # 2, actual value, e.g. 200
        expect_value = self.eval_content(validator["expect"])
        validator["expect"] = expect_value
        validator["check_result"] = "unchecked"
        return validator

    def _do_validation(self, validator_dict):
        """ validate with functions

        Args:
            validator_dict (dict): validator dict
                {
                    "check": "status_code",
                    "check_value": 200,
                    "expect": 201,
                    "comparator": "eq"
                }

        """
        # TODO: move comparator uniform to init_test_suites
        comparator = utils.get_uniform_comparator(validator_dict["comparator"])
        validate_func = parser.get_mapping_function(comparator, self.FUNCTIONS_MAPPING)

        check_item = validator_dict["check"]
        check_value = validator_dict["check_value"]
        expect_value = validator_dict["expect"]
        check_value_type, expect_value_type = type(check_value).__name__, type(expect_value).__name__

        try:
            validator_dict["check_result"] = "pass"
            validate_func(check_value, expect_value)
            logger.log_debug(f"断言: "
                             f"{check_item} "
                             f"{getattr(built_in, comparator).__doc__} "
                             f"{expect_value}({type(expect_value).__name__}) "
                             f"==> pass")
        except (AssertionError, TypeError) as error:
            # 方便在页面上对比，转为dict
            try:
                if isinstance(expect_value, str):
                    expect_value = json.loads(expect_value)
            except Exception as json_loads_error:
                pass

            error_msg = f"""
            断言不通过\n
            断言方式: {getattr(built_in, comparator).__doc__}\n
            预期结果: {expect_value}({expect_value_type})\n
            实际结果: {check_value}({check_value_type})\n
            描述：{error}
            """
            # 断言结果: {error}  # 断言未通过，断言方式为相等
            validator_dict["check_result"] = "fail"
            raise exceptions.ValidationFailure(error_msg)

    def validate(self, validators, resp_obj):
        """ 执行断言 """
        self.validation_results = []
        if not validators:
            return

        logger.log_debug("开始断言")

        validate_pass = True
        failures = []

        for validator in validators:
            # evaluate validators with context variable mapping.
            evaluated_validator = self.__eval_check_item(parser.parse_validator(validator), resp_obj)
            try:
                self._do_validation(evaluated_validator)
            except exceptions.ValidationFailure as ex:
                validate_pass = False
                failures.append(str(ex))

            self.validation_results.append(evaluated_validator)

        if not validate_pass:  # 断言未通过
            failures_string = "\n".join([failure for failure in failures])
            raise exceptions.ValidationFailure(failures_string)
