# encoding: utf-8

import ast
import re

from . import exceptions, utils
from .compat import basestring, builtin_str, numeric_types, str

variable_regexp = r"\$([\w_]+)"  # 变量
function_regexp = r"\$\{([\w_]+\([\$\w\.\-/_ =,]*\))\}"  # 自定义函数
function_regexp_compile = re.compile(r"^([\w_]+)\(([\$\w\.\-/_ =,]*)\)$")


def parse_string_value(str_value):
    """ 把能转成数字的字符串转成数字
    e.g. "123" => 123
         "12.2" => 12.3
         "abc" => "abc"
         "$var" => "$var"
    """
    try:
        if '-' in str_value:
            return str_value
        else:
            return ast.literal_eval(str_value)
    except ValueError:
        return str_value
    except SyntaxError:
        # e.g. $var, ${func}
        return str_value


def extract_variables(content):
    """ 从content中提取所有变量名为$variable的变量
    Args:
        content (str): 字符串
    Returns:
        list: 从字符串内容中提取的变量列表
    Examples:
        >>> extract_variables("$variable")
        ["variable"]
        >>> extract_variables("/blog/$postid")
        ["postid"]
        >>> extract_variables("/$var1/$var2")
        ["var1", "var2"]
        >>> extract_variables("abc")
        []
    """
    # TODO: change variable notation from $var to {{var}}
    try:
        return re.findall(variable_regexp, content)
    except TypeError:
        return []


def extract_functions(content):
    """ 从content中提取所有变量名为${fun()}的函数
    Args:
        content (str): 字符串
    Returns:
        list: 从字符串内容中提取的函数列表
    Examples:
        >>> extract_functions("${func(5)}")
        ["func(5)"]
        >>> extract_functions("${func(a=1, b=2)}")
        ["func(a=1, b=2)"]
        >>> extract_functions("/api/1000?_t=${get_timestamp()}")
        ["get_timestamp()"]
        >>> extract_functions("/api/${add(1, 2)}")
        ["add(1, 2)"]
        >>> extract_functions("/api/${add(1, 2)}?_t=${get_timestamp()}")
        ["add(1, 2)", "get_timestamp()"]
    """
    try:
        return re.findall(function_regexp, content)
    except TypeError:
        return []


def parse_function(content):
    """ 从字符串内容中解析函数名和参数。
    Args:
        content (str): 字符串
    Returns:
        dict: 字典格式的函数名和参数
            {
                "func_name": "xxx",
                "args": [],
                "kwargs": {}
            }
    Examples:
        >>> parse_function("func()")
        {'func_name': 'func', 'args': [], 'kwargs': {}}
        >>> parse_function("func(5)")
        {'func_name': 'func', 'args': [5], 'kwargs': {}}
        >>> parse_function("func(1, 2)")
        {'func_name': 'func', 'args': [1, 2], 'kwargs': {}}
        >>> parse_function("func(a=1, b=2)")
        {'func_name': 'func', 'args': [], 'kwargs': {'a': 1, 'b': 2}}
        >>> parse_function("func(1, 2, a=3, b=4)")
        {'func_name': 'func', 'args': [1, 2], 'kwargs': {'a':3, 'b':4}}
    """
    matched = function_regexp_compile.match(content)
    if not matched:
        raise exceptions.FunctionNotFound("{} not found!".format(content))
    function_meta = {"func_name": matched.group(1), "args": [], "kwargs": {}}
    args_str = matched.group(2).strip()
    if args_str == "":
        return function_meta
    args_list = args_str.split(',')
    for arg in args_list:
        arg = arg.strip()
        if '=' in arg:
            key, value = arg.split('=')
            function_meta["kwargs"][key.strip()] = parse_string_value(value.strip())
        else:
            function_meta["args"].append(parse_string_value(arg))

    return function_meta


def parse_validator(validator):
    """
    解析验证器
    Args:
        {
            "comparator": "assert_56text_in_value",  # 断言方式
            "check": ("id", "kw"),   # 实际结果
            "expect": "123123"   # 预期结果
        }

    Returns:
        {
            "comparator": "assert_56text_in_value",  # 断言方式
            "check": ("id", "kw"),   # 实际结果
            "expect": "123123"   # 预期结果
        }
    """
    validator_parse_error = exceptions.ParamsError(f"验证器错误: {validator}")
    if not isinstance(validator, dict):
        raise validator_parse_error

    if "comparator" not in validator or "check" not in validator or "expect" not in validator:
        raise validator_parse_error

    return validator


def substitute_variables(content, variables_mapping):
    """ substitute variables in content with variables_mapping

    Args:
        content (str/dict/list/numeric/bool/type): content to be substituted.
        variables_mapping (dict): variables mapping.

    Returns:
        substituted content.

    Examples:
        >>> content = {
                'request': {
                    'url': '/api/users/$uid',
                    'headers': {'token': '$token'}
                }
            }
        >>> variables_mapping = {"$uid": 1000}
        >>> substitute_variables(content, variables_mapping)
            {
                'request': {
                    'url': '/api/users/1000',
                    'headers': {'token': '$token'}
                }
            }

    """
    if isinstance(content, (list, set, tuple)):
        return [
            substitute_variables(item, variables_mapping)
            for item in content
        ]

    if isinstance(content, dict):
        substituted_data = {}
        for key, value in content.items():
            eval_key = substitute_variables(key, variables_mapping)
            eval_value = substitute_variables(value, variables_mapping)
            substituted_data[eval_key] = eval_value

        return substituted_data

    if isinstance(content, basestring):
        # content is in string format here
        for var, value in variables_mapping.items():
            if content == var:
                # content is a variable
                content = value
            else:
                if not isinstance(value, str):
                    value = builtin_str(value)
                content = content.replace(var, value)

    return content


def parse_parameters(parameters, variables_mapping=None, functions_mapping=None):
    """ parse parameters and generate cartesian product.

    Args:
        parameters (list) parameters: parameter name and value in list
            parameter value may be in three types:
                (1) data list, e.g. ["iOS/10.1", "iOS/10.2", "iOS/10.3"]
                (2) call built-in parameterize function, "${parameterize(account.csv)}"
                (3) call custom function in debugtalk.py, "${gen_app_version()}"

        variables_mapping (dict): variables mapping loaded from testcase config
        functions_mapping (dict): functions mapping loaded from debugtalk.py

    Returns:
        list: cartesian product list

    Examples:
        >>> parameters = [
            {"user_agent": ["iOS/10.1", "iOS/10.2", "iOS/10.3"]},
            {"username-password": "${parameterize(account.csv)}"},
            {"app_version": "${gen_app_version()}"}
        ]
        >>> parse_parameters(parameters)

    """
    variables_mapping = variables_mapping or {}
    functions_mapping = functions_mapping or {}
    parsed_parameters_list = []

    parameters = utils.ensure_mapping_format(parameters)
    for parameter_name, parameter_content in parameters.items():
        parameter_name_list = parameter_name.split("-")

        if isinstance(parameter_content, list):
            # (1) data list
            # e.g. {"app_version": ["2.8.5", "2.8.6"]}
            #       => [{"app_version": "2.8.5", "app_version": "2.8.6"}]
            # e.g. {"username-password": [["user1", "111111"], ["test2", "222222"]}
            #       => [{"username": "user1", "password": "111111"}, {"username": "user2", "password": "222222"}]
            parameter_content_list = []
            for parameter_item in parameter_content:
                if not isinstance(parameter_item, (list, tuple)):
                    # "2.8.5" => ["2.8.5"]
                    parameter_item = [parameter_item]

                # ["app_version"], ["2.8.5"] => {"app_version": "2.8.5"}
                # ["username", "password"], ["user1", "111111"] => {"username": "user1", "password": "111111"}
                parameter_content_dict = dict(zip(parameter_name_list, parameter_item))

                parameter_content_list.append(parameter_content_dict)
        else:
            # (2) & (3)
            parsed_parameter_content = parse_data(parameter_content, variables_mapping, functions_mapping)
            if not isinstance(parsed_parameter_content, list):
                raise exceptions.ParamsError("parameters syntax error!")

            parameter_content_list = []
            for parameter_item in parsed_parameter_content:
                if isinstance(parameter_item, dict):
                    # get subset by parameter name
                    # {"app_version": "${gen_app_version()}"}
                    # gen_app_version() => [{'app_version': '2.8.5'}, {'app_version': '2.8.6'}]
                    # {"username-password": "${get_account()}"}
                    # get_account() => [
                    #       {"username": "user1", "password": "111111"},
                    #       {"username": "user2", "password": "222222"}
                    # ]
                    parameter_dict = {key: parameter_item[key] for key in parameter_name_list}
                elif isinstance(parameter_item, (list, tuple)):
                    # {"username-password": "${get_account()}"}
                    # get_account() => [("user1", "111111"), ("user2", "222222")]
                    parameter_dict = dict(zip(parameter_name_list, parameter_item))
                elif len(parameter_name_list) == 1:
                    # {"user_agent": "${get_user_agent()}"}
                    # get_user_agent() => ["iOS/10.1", "iOS/10.2"]
                    parameter_dict = {
                        parameter_name_list[0]: parameter_item
                    }

                parameter_content_list.append(parameter_dict)

        parsed_parameters_list.append(parameter_content_list)

    return utils.gen_cartesian_product(*parsed_parameters_list)


##############################################################################
#  parse content with variables and functions mapping
##############################################################################

def get_mapping_variable(variable_name, variables_mapping):
    """ 从变量映射中获取变量值

    Args:
        variable_name (str): variable name
        variables_mapping (dict): variables mapping
    Returns:
        映射变量的值
    Raises:
        exceptions.VariableNotFound: 找不到变量
    """
    try:
        return variables_mapping[variable_name]
    except KeyError:
        raise exceptions.VariableNotFound(f"引用的变量 {variable_name} 没有找到")


def get_mapping_function(function_name, functions_mapping):
    """ get function from functions_mapping,
        if not found, then try to check if builtin function.

    Args:
        variable_name (str): variable name
        variables_mapping (dict): variables mapping

    Returns:
        mapping function object.

    Raises:
        exceptions.FunctionNotFound: function is neither defined in debugtalk.py nor builtin.

    """
    if function_name in functions_mapping:
        return functions_mapping[function_name]

    try:
        # check if HttpRunner builtin functions
        from . import loader
        built_in_functions = loader.load_builtin_functions()
        return built_in_functions[function_name]
    except KeyError:
        pass

    try:
        # check if Python builtin functions
        item_func = eval(function_name)
        if callable(item_func):
            # is builtin function
            return item_func
    except (NameError, TypeError):
        # is not builtin function
        raise exceptions.FunctionNotFound(f"自定义函数 {function_name} 没有找到")


def parse_string_functions(content: str, variables_mapping: dict, functions_mapping: dict):
    """ 映射字符串中的函数
    Args:
        content (str): 要解析的字符串内容
        variables_mapping (dict): 映射变量
        functions_mapping (dict): 映射函数
    Returns:
        str: 解析后的字符串
    Examples:
        >>> content = "abc${add_one(3)}def"
        >>> functions_mapping = {"add_one": lambda x: x + 1}
        >>> parse_string_functions(content, functions_mapping)
            "abc4def"
    """
    functions_list = extract_functions(content)
    for func_content in functions_list:
        function_meta = parse_function(func_content)
        func_name = function_meta["func_name"]

        args = function_meta.get("args", [])
        kwargs = function_meta.get("kwargs", {})
        args = parse_data(args, variables_mapping, functions_mapping)
        kwargs = parse_data(kwargs, variables_mapping, functions_mapping)

        if func_name in ["parameterize", "P"]:
            if len(args) != 1 or kwargs:
                raise exceptions.ParamsError("P() should only pass in one argument!")
            from . import loader
            eval_value = loader.load_csv_file(args[0])
        elif func_name in ["environ", "ENV"]:
            if len(args) != 1 or kwargs:
                raise exceptions.ParamsError("ENV() should only pass in one argument!")
            eval_value = utils.get_os_environ(args[0])
        else:
            func = get_mapping_function(func_name, functions_mapping)
            # eval_value = func(*args, **kwargs)
            # 执行自定义函数，有可能会报错
            try:
                eval_value = func(*args, **kwargs)
            except Exception as error:
                # 记录错误信息
                # ErrorRecord().create({
                #     'name': '执行自定义函数错误',
                #     'detail': f'执行自定义函数【{func_name}】报错了 \n  args参数: {args} \n  kwargs参数: {kwargs} \n\n  '
                #               f'错误信息: \n{traceback.format_exc()}'
                # })
                #
                # # 发送自定义函数执行错误的信息
                # async_send_run_time_error_message(content={
                #     "title": "执行自定义函数错误",
                #     "detail": f'### {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} \n> '
                #               f'### 执行自定义函数【{func_name}】报错了 \n  args参数: {args} \n  kwargs参数: {kwargs} \n  '
                #               f'### 错误信息: {traceback.format_exc()} \n> '
                # }, addr=Config.get_first(name='run_time_error_message_send_addr').value)
                raise

        func_content = "${" + func_content + "}"
        if func_content == content:
            # content is a function, e.g. "${add_one(3)}"
            content = eval_value
        else:
            # content contains one or many functions, e.g. "abc${add_one(3)}def"
            content = content.replace(
                func_content,
                str(eval_value), 1
            )

    return content


def parse_string_variables(content: str, variables_mapping: dict, functions_mapping: dict):
    """ 从字符串中，解析引用变量

    Args:
        content (str): string content to be parsed.
        variables_mapping (dict): variables mapping.

    Returns:
        str: parsed string content.

    Examples:
        >>> content = "/api/users/$uid"
        >>> variables_mapping = {"$uid": 1000}
        >>> parse_string_variables(content, variables_mapping, {})
            "/api/users/1000"

    """
    variables_list = extract_variables(content)
    for variable_name in variables_list:
        variable_value = get_mapping_variable(variable_name, variables_mapping)

        if variable_name == "request" and isinstance(variable_value, dict) \
                and "url" in variable_value and "method" in variable_value:
            # call setup_hooks action with $request
            for key, value in variable_value.items():
                variable_value[key] = parse_data(
                    value,
                    variables_mapping,
                    functions_mapping
                )
            parsed_variable_value = variable_value
        elif "${}".format(variable_name) == variable_value:
            # variable_name = "token"
            # variables_mapping = {"token": "$token"}
            parsed_variable_value = variable_value
        else:
            parsed_variable_value = parse_data(
                variable_value,
                variables_mapping,
                functions_mapping,
                raise_if_variable_not_found=False
            )
            variables_mapping[variable_name] = parsed_variable_value
        # TODO: replace variable label from $var to {{var}}
        if "${}".format(variable_name) == content:
            # content is a variable
            content = parsed_variable_value
        else:
            # content contains one or several variables
            if not isinstance(parsed_variable_value, str):
                parsed_variable_value = builtin_str(parsed_variable_value)

            content = content.replace(
                "${}".format(variable_name),
                parsed_variable_value, 1
            )

    return content


def parse_data(content, variables_mapping=None, functions_mapping=None, raise_if_variable_not_found=True):
    """ 用变量映射解析内容
    Args:
        content (str/dict/list/numeric/bool/type): 要解析的内容
        variables_mapping (dict): 变量映射
        functions_mapping (dict): 方法映射
        raise_if_variable_not_found (bool): 如果设置为False，则在发生VariableNotFound异常时不会抛出。
    Returns:
        解析后的内容

    Examples:
        >>> content = {
                'request': {
                    'url': '/api/users/$uid',
                    'headers': {'token': '$token'}
                }
            }
        >>> variables_mapping = {"uid": 1000, "token": "abcdef"}
        >>> parse_data(content, variables_mapping)
            {
                'request': {
                    'url': '/api/users/1000',
                    'headers': {'token': 'abcdef'}
                }
            }

    """
    # TODO: refactor type check
    if content is None or isinstance(content, (numeric_types, bool, type)):
        return content

    if isinstance(content, (list, set, tuple)):
        return [
            parse_data(
                item,
                variables_mapping,
                functions_mapping,
                raise_if_variable_not_found
            )
            for item in content
        ]

    if isinstance(content, dict):
        parsed_content = {}
        for key, value in content.items():
            parsed_key = parse_data(
                key,
                variables_mapping,
                functions_mapping,
                raise_if_variable_not_found
            )
            parsed_value = parse_data(
                value,
                variables_mapping,
                functions_mapping,
                raise_if_variable_not_found
            )
            parsed_content[parsed_key] = parsed_value

        return parsed_content

    if isinstance(content, basestring):
        # content is in string format here
        variables_mapping = utils.ensure_mapping_format(variables_mapping or {})
        functions_mapping = functions_mapping or {}
        content = content.strip()

        try:
            # 提取并执行自定义函数
            content = parse_string_functions(
                content,
                variables_mapping,
                functions_mapping
            )
            # 用公用变量替换字符串中的占位符
            content = parse_string_variables(
                content,
                variables_mapping,
                functions_mapping
            )
        except exceptions.VariableNotFound:
            if raise_if_variable_not_found:
                raise

    return content


def __parse_config(config: dict, project_mapping: dict):
    """ 解析 testcase 的配置, 包括变量和名称。
    config：testcase的config
    """
    # 获取配置的变量
    case_config_variables = config.pop("variables", {})
    case_config_variables_mapping = utils.ensure_mapping_format(case_config_variables)
    project_config_variables = utils.deepcopy_dict(project_mapping.get("variables", {}))
    case_config_variables_mapping.update(project_config_variables)  # 合并变量

    functions = project_mapping.get("functions", {})

    # 解析变量
    parsed_config_variables = {}

    for key in case_config_variables_mapping:
        parsed_value = parse_data(
            case_config_variables_mapping[key],
            case_config_variables_mapping,
            functions,
            raise_if_variable_not_found=False
        )
        case_config_variables_mapping[key] = parsed_value
        parsed_config_variables[key] = parsed_value

    if parsed_config_variables:
        config["variables"] = parsed_config_variables

    # parse config name
    config["name"] = parse_data(config.get("name", ""), parsed_config_variables, functions)


def __parse_steps(steps: list, case_config: dict, project_mapping: dict):
    """ 使用配置来解析测试数据
        test_dicts:
            [{
              "extract": [{"c": "content.c"}],
              "name": "post请求",
              "action": {
                "action": "click",
                "by_type": "by_type",
                "element": "element",
                "text": "text"
              },
              "times": 1,
              "validate": [{"equals": ["$c", 3]}]
            }]
    """
    # 用例中配置的浏览器信息
    web_driver_time_out = case_config.get("web_driver_time_out", '')
    browser_type, browser_path = case_config.get("browser_type", ''), case_config.get("browser_path", '')

    # 用例中配置变量、自定义函数
    config_variables, functions = case_config.get("variables", {}), project_mapping.get("functions", {})

    for step in steps:

        # 合并自定义变量
        step["variables"] = utils.extend_variables(step.pop("variables", {}), config_variables)

        # 把浏览器相关信息加到步骤中
        step.setdefault("browser_type", browser_type)
        step.setdefault("browser_path", browser_path)
        step.setdefault("web_driver_time_out", web_driver_time_out)

        # 处理变量本身，有变量本身就有引用变量的情况
        for key in step["variables"]:
            parsed_key = parse_data(
                key,
                step["variables"],
                functions,
                raise_if_variable_not_found=False
            )
            parsed_value = parse_data(
                step["variables"][key],
                step["variables"],
                functions,
                raise_if_variable_not_found=False
            )
            if parsed_key in step["variables"]:
                step["variables"][parsed_key] = parsed_value

        # 测试步骤名字
        step["name"] = parse_data(
            step.pop("name", ""),
            step["variables"],
            functions,
            raise_if_variable_not_found=False
        )


def _parse_testcase(testcase: dict, project_mapping: dict):
    """ 解析测试用例
    Args:
        testcase (dict):
            {
                "config": {},
                "teststeps": []
            }

    """
    testcase.setdefault("config", {})
    __parse_config(testcase["config"], project_mapping)
    __parse_steps(testcase["teststeps"], testcase["config"], project_mapping)


def parse_tests(tests_mapping: dict):
    """ 解析测试数据和测试用例
    Args:
        tests_mapping (dict): 项目信息和用例list

            {
                "project_mapping": {
                    "PWD": "XXXXX",
                    "functions": {},
                    "variables": {},                        # optional, priority 1
                    "env": {}
                },
                "testcases": [
                    {   # testcase data structure
                        "config": {
                            "name": "desc1",
                            "browser_type": "chrome",
                            "browser_path": r"D:\browserdriver\chromedriver.exe",
                            "variables": {},                # optional, priority 2
                        },
                        "teststeps": [
                            # test data structure
                            {
                                'name': 'test step desc1',
                                'variables': [],            # optional, priority 3
                                'extract': [],
                                'validate': [],
                                'api_def': {
                                    "variables": {}         # optional, priority 4
                                    'request': {},
                                }
                            }
                        ]
                    }
                ]
            }

    """
    project_mapping = tests_mapping.get("project_mapping", {})
    parsed_tests_mapping = {
        "project": tests_mapping.get("project", {}),
        "project_mapping": project_mapping,
        "testcases": []
    }

    for testcase in tests_mapping["testcases"]:
        _parse_testcase(testcase, project_mapping)
        parsed_tests_mapping["testcases"].append(testcase)

    return parsed_tests_mapping
