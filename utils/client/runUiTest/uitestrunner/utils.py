# # encoding: utf-8

import copy
import io
import itertools
import json
import os.path

from . import exceptions, logger
from .exceptions import ParamsError
from utils.variables.regexp import absolute_http_url_regexp


def get_os_environ(variable_name):
    """ get value of environment variable.

    Args:
        variable_name(str): variable name

    Returns:
        value of environment variable.

    Raises:
        exceptions.EnvNotFound: If environment variable not found.

    """
    try:
        return os.environ[variable_name]
    except KeyError:
        raise exceptions.EnvNotFound(variable_name)


def lower_dict_keys(origin_dict):
    """ convert keys in dict to lower case

    Args:
        origin_dict (dict): mapping data structure

    Returns:
        dict: mapping with all keys lowered.

    Examples:
        >>> origin_dict = {
            "Name": "",
            "Request": "",
            "URL": "",
            "METHOD": "",
            "Headers": "",
            "Data": ""
        }
        >>> lower_dict_keys(origin_dict)
            {
                "name": "",
                "request": "",
                "url": "",
                "method": "",
                "headers": "",
                "data": ""
            }

    """
    if not origin_dict or not isinstance(origin_dict, dict):
        return origin_dict

    return {
        key.lower(): value
        for key, value in origin_dict.items()
    }


def build_url(base_url, path):
    """ 在接口路由前面加上主机名，若设置的接口信息已包含域名，则直接返回 """
    if absolute_http_url_regexp.match(path):
        return path
    elif base_url:
        return "{}/{}".format(base_url.rstrip("/"), path.lstrip("/"))
    else:
        raise ParamsError(f"域名 '{base_url}' 错误, 请检查服务信息")


def deepcopy_dict(data):
    """ 返回深拷贝文件，其中忽略io对象
    Args:
            {
                'a': 1,
                'b': [2, 4],
                'c': lambda x: x+1,
                'd': open('LICENSE'),
                'f': {
                    'f1': {'a1': 2},
                    'f2': io.open('LICENSE', 'rb'),
                }
            }

    Returns:
            {
                'a': 1,
                'b': [2, 4],
                'c': lambda x: x+1,
                'd': open('LICENSE'),
                'f': {
                    'f1': {'a1': 2}
                }
            }

    """
    try:
        return copy.deepcopy(data)
    except TypeError:
        copied_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                copied_data[key] = deepcopy_dict(value)
            else:
                try:
                    copied_data[key] = copy.deepcopy(value)
                except TypeError:
                    copied_data[key] = value

        return copied_data


def ensure_mapping_format(variables):
    """ 把list的变量转化为dict
    Args:
        variables (list/dict): original variables
    Returns:
        dict: ensured variables in dict format
    Examples:
        >>> variables = [
                {"a": 1},
                {"b": 2}
            ]
        >>> print(ensure_mapping_format(variables))
            {
                "a": 1,
                "b": 2
            }
    """
    if isinstance(variables, list):
        variables_dict = {}
        for map_dict in variables:
            variables_dict.update(map_dict)
        return variables_dict

    elif isinstance(variables, dict):
        return variables

    else:
        raise exceptions.ParamsError("变量格式错误")


def extend_variables(raw_variables: list, override_variables: list):
    """ raw_variables转为dict后 继承 override_variables转为dict后的值
    Examples:
        >>> raw_variables = [{"var1": "val1"}, {"var2": "val2"}]
        >>> override_variables = [{"var1": "val111"}, {"var3": "val3"}]
        >>> extend_variables(raw_variables, override_variables)
            {
                'var1', 'val111',
                'var2', 'val2',
                'var3', 'val3'
            }
    """
    if not raw_variables:
        override_variables_mapping = ensure_mapping_format(override_variables)
        return override_variables_mapping

    elif not override_variables:
        raw_variables_mapping = ensure_mapping_format(raw_variables)
        return raw_variables_mapping

    else:
        raw_variables_mapping = ensure_mapping_format(raw_variables)
        override_variables_mapping = ensure_mapping_format(override_variables)
        raw_variables_mapping.update(override_variables_mapping)
        return raw_variables_mapping


def get_testcase_io(testcase):
    """ get and print testcase input(variables) and output.

    Args:
        testcase (unittest.suite.TestSuite): corresponding to one YAML/JSON file, it has been set two attributes:
            config: parsed config block
            runner: initialized runner.Runner() with config
    Returns:
        dict: input(variables) and output mapping.

    """
    test_runner = testcase.runner
    variables = testcase.config.get("variables", {})
    output_list = testcase.config.get("output", [])
    output_mapping = test_runner.extract_output(output_list)

    return {
        "in": variables,
        "out": output_mapping
    }


def print_info(info_mapping: dict):
    """ 打印映射信息

    Args:
        info_mapping (dict): input(variables) or output mapping.

    Examples:
        >>> info_mapping = {
                "var_a": "hello",
                "var_b": "world"
            }
        >>> info_mapping = {
                "status_code": 500
            }
        >>> print_info(info_mapping)
        ==================== Output ====================
        Key              :  Value
        ---------------- :  ----------------------------
        var_a            :  hello
        var_b            :  world
        ------------------------------------------------

    """
    if not info_mapping:
        return

    content_format = "{:<16} : {:<}\n"
    content = "\n==================== Output ====================\n"
    content += content_format.format("Variable", "Value")
    content += content_format.format("-" * 16, "-" * 29)

    for key, value in info_mapping.items():
        if isinstance(value, (tuple, collections.deque)):
            continue
        elif isinstance(value, (dict, list)):
            value = json.dumps(value)

        content += content_format.format(key, value)

    content += "-" * 48 + "\n"
    logger.log_info(content)


def gen_cartesian_product(*args):
    """ generate cartesian product for lists

    Args:
        args (list of list): lists to be generated with cartesian product

    Returns:
        list: cartesian product in list

    Examples:

        >>> arg1 = [{"a": 1}, {"a": 2}]
        >>> arg2 = [{"x": 111, "y": 112}, {"x": 121, "y": 122}]
        >>> args = [arg1, arg2]
        >>> gen_cartesian_product(*args)
        >>> # same as below
        >>> gen_cartesian_product(arg1, arg2)
            [
                {'a': 1, 'x': 111, 'y': 112},
                {'a': 1, 'x': 121, 'y': 122},
                {'a': 2, 'x': 111, 'y': 112},
                {'a': 2, 'x': 121, 'y': 122}
            ]

    """
    if not args:
        return []
    elif len(args) == 1:
        return args[0]

    product_list = []
    for product_item_tuple in itertools.product(*args):
        product_item_dict = {}
        for item in product_item_tuple:
            product_item_dict.update(item)

        product_list.append(product_item_dict)

    return product_list


def omit_long_data(body, omit_len=512):
    """ omit too long str/bytes """
    if not isinstance(body, basestring):
        return body

    body_len = len(body)
    if body_len <= omit_len:
        return body

    omitted_body = body[0:omit_len]

    appendix_str = " ... OMITTED {} CHARACTORS ...".format(body_len - omit_len)
    if isinstance(body, bytes):
        appendix_str = appendix_str.encode("utf-8")

    return omitted_body + appendix_str


def dump_json_file(json_data, pwd_dir_path, dump_file_name):
    """ dump json data to file """
    logs_dir_path = os.path.join(pwd_dir_path, "logs")
    if not os.path.isdir(logs_dir_path):
        os.makedirs(logs_dir_path)

    dump_file_path = os.path.join(logs_dir_path, dump_file_name)

    try:
        with io.open(dump_file_path, 'w', encoding='utf-8') as outfile:
            json.dump(
                json_data,
                outfile,
                indent=4,
                separators=(',', ':'),
                ensure_ascii=False
            )

        msg = "dump file: {}".format(dump_file_path)
        logger.color_print(msg, "BLUE")

    except TypeError:
        msg = "Failed to dump json file: {}".format(dump_file_path)
        logger.color_print(msg, "RED")


def _prepare_dump_info(project_mapping, tag_name):
    """ prepare dump file info """
    test_path = project_mapping.get("test_path") or "tests_mapping"
    pwd_dir_path = project_mapping.get("PWD") or os.getcwd()
    file_name, file_suffix = os.path.splitext(os.path.basename(test_path.rstrip("/")))
    dump_file_name = "{}.{}.json".format(file_name, tag_name)

    return pwd_dir_path, dump_file_name


def dump_summary(summary, project_mapping):
    """ 把测试数据和结果存到json文件 """
    pwd_dir_path, dump_file_name = _prepare_dump_info(project_mapping, "summary")
    dump_json_file(summary, pwd_dir_path, dump_file_name)
