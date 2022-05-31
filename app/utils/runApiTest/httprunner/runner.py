# encoding: utf-8
import copy
from unittest.case import SkipTest

from . import exceptions, logger, response, utils
from .client import HttpSession
from .context import SessionContext


class Runner(object):
    """ Running testcases.

    Examples:
        >>> functions={...}
        >>> config = {
                "name": "XXXX",
                "base_url": "http://127.0.0.1",
                "verify": False
            }
        >>> runner = Runner(config, functions)

        >>> test_dict = {
                "name": "test description",
                "variables": [],        # optional
                "request": {
                    "url": "http://127.0.0.1:5000/api/users/1000",
                    "method": "GET"
                }
            }
        >>> runner.run_test(test_dict)

    """

    def __init__(self, config, functions, http_client_session=None):
        """ run testcase or testsuite.

        Args:
            config (dict): testcase/testsuite config dict

                {
                    "name": "ABC",
                    "variables": {},
                    "setup_hooks", [],
                    "teardown_hooks", []
                }

            http_client_session (instance): requests.Session(), or locust.client.Session() instance.

        """
        base_url = config.get("base_url")
        self.verify = config.get("verify", True)
        self.output = config.get("output", [])
        self.functions = functions
        self.validation_results = []

        # testcase setup hooks
        testcase_setup_hooks = config.get("setup_hooks", [])
        # testcase teardown hooks
        self.testcase_teardown_hooks = config.get("teardown_hooks", [])

        self.http_client_session = http_client_session or HttpSession(base_url)
        self.session_context = SessionContext(self.functions)

        if testcase_setup_hooks:
            self.do_hook_actions(testcase_setup_hooks, "setup")

    def __del__(self):
        if self.testcase_teardown_hooks:
            self.do_hook_actions(self.testcase_teardown_hooks, "teardown")

    def __clear_test_data(self):
        """ 清除请求和响应数据 """
        if not isinstance(self.http_client_session, HttpSession):
            return

        self.validation_results = []
        self.http_client_session.init_meta_data()

    def __get_test_data(self):
        """ get request/response data and validate results
        """
        if not isinstance(self.http_client_session, HttpSession):
            return

        meta_data = self.http_client_session.meta_data
        meta_data["validators"] = self.validation_results
        return meta_data

    def _handle_skip_feature(self, test_dict):
        """ handle skip feature for test
            - skip: skip current test unconditionally
            - skipIf: skip current test if condition is true
            - skipUnless: skip current test unless condition is true

        Args:
            test_dict (dict): test info

        Raises:
            SkipTest: skip test

        """
        # TODO: move skip to initialize
        skip_reason = None

        if "skip" in test_dict:
            skip_reason = test_dict["skip"]

        elif "skipIf" in test_dict:
            skip_if_condition = test_dict["skipIf"]
            if self.session_context.eval_content(skip_if_condition):
                skip_reason = "{} evaluate to True".format(skip_if_condition)

        elif "skipUnless" in test_dict:
            skip_unless_condition = test_dict["skipUnless"]
            if not self.session_context.eval_content(skip_unless_condition):
                skip_reason = "{} evaluate to False".format(skip_unless_condition)

        if skip_reason:
            raise SkipTest(skip_reason)

    def do_hook_actions(self, actions, hook_type):
        """ 执行自定义函数

        Args:
            actions (list): each action in actions list maybe in two format.

                format1 (dict): assignment, the value returned by hook function will be assigned to variable.
                    {"var": "${func()}"}
                format2 (str): only call hook functions.
                    ${func()}

            hook_type (enum): setup/teardown

        """
        logger.log_debug(f"执行 {hook_type} 类型函数")
        for action in actions:

            if isinstance(action, dict) and len(action) == 1:
                # format 1
                # {"var": "${func()}"}
                var_name, hook_content = list(action.items())[0]
                hook_content_eval = self.session_context.eval_content(hook_content)
                logger.log_debug(
                    "assignment with hook: {} = {} => {}".format(
                        var_name, hook_content, hook_content_eval
                    )
                )
                self.session_context.update_test_variables(
                    var_name, hook_content_eval
                )
            else:
                # format 2
                logger.log_debug(f"执行自定义函数 {action}")
                # TODO: check hook function if valid
                self.session_context.eval_content(action)

    def _run_test(self, test_dict):
        """ 单个teststep运行。

        Args:
            test_dict (dict): teststep info
                {
                    "name": "teststep description",
                    "skip": "skip this test unconditionally",
                    "times": 3,
                    "variables": [],            # optional, override
                    "request": {
                        "url": "http://127.0.0.1:5000/api/users/1000",
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json",
                            "authorization": "$authorization",
                            "random": "$random"
                        },
                        "json": {"name": "user", "password": "123456"}
                    },
                    "extract": {},              # optional
                    "validate": [],             # optional
                    "setup_hooks": [],          # optional
                    "teardown_hooks": []        # optional
                }

        Raises:
            exceptions.ParamsError
            exceptions.ValidationFailure
            exceptions.ExtractFailure

        """
        # clear meta data first to ensure independence for each test
        self.__clear_test_data()
        # print(test_dict)
        # prepare
        # test_dict = utils.lower_test_dict_keys(test_dict)
        test_variables = test_dict.get("variables", {})
        self.session_context.init_test_variables(test_variables)

        # check skip
        # if test_dict.get('skipIf'):
        #     test_dict['skipIf'] = self.session_context.eval_content(test_dict['skipIf'])
        self._handle_skip_feature(test_dict)

        # teststep name
        test_name = test_dict.get("name", "")

        # 解析请求，替换变量、自定义函数
        raw_request = test_dict.get('request', {})
        parsed_test_request = self.session_context.eval_content(raw_request)
        self.session_context.update_test_variables("request", parsed_test_request)

        # 如果请求体是字符串（xml），转为utf-8格式
        if isinstance(parsed_test_request['data'], str):
            parsed_test_request['data'] = parsed_test_request['data'].encode('utf-8')

        # 执行前置函数
        setup_hooks = test_dict.get("setup_hooks", [])
        if setup_hooks:
            self.do_hook_actions(setup_hooks, "setup")

        try:
            url = parsed_test_request.pop('url')
            method = parsed_test_request.pop('method')
            parsed_test_request.setdefault("verify", self.verify)
            group_name = parsed_test_request.pop("group", None)
        except KeyError:
            raise exceptions.ParamsError("URL or METHOD missed!")

        # TODO: move method validation to json schema
        valid_methods = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
        if method.upper() not in valid_methods:
            err_msg = f"请求方法 {method} 错误，仅支持{'/'.join(valid_methods)}"
            logger.log_error(err_msg)
            raise exceptions.ParamsError(err_msg)

        logger.log_info(f"{method} {url}")
        logger.log_debug("request kwargs(raw): {kwargs}".format(kwargs=parsed_test_request))

        # 深拷贝除 request 的其他数据，请求数据有可能是io，io不能深拷贝，所以先移出再深拷贝，再移入
        request = self.session_context.test_variables_mapping.pop('request')
        variables_mapping = copy.deepcopy(self.session_context.test_variables_mapping)
        self.session_context.test_variables_mapping['request'] = request

        # 发送请求
        resp = self.http_client_session.request(
            method,
            url,
            name=(group_name or test_name),
            variables_mapping=copy.deepcopy(variables_mapping),
            **parsed_test_request
        )

        resp_obj = response.ResponseObject(resp)

        # 数据提取
        extractors = test_dict.get("extract", {})
        extracted_variables_mapping = resp_obj.extract_response(self.session_context, extractors)
        self.http_client_session.meta_data['data'][0]['extract_msgs'] = extracted_variables_mapping
        # setattr(resp_obj, 'extractors',extracted_variables_mapping)
        self.session_context.update_session_variables(extracted_variables_mapping)

        # 后置函数
        teardown_hooks = test_dict.get("teardown_hooks", [])
        if teardown_hooks:
            self.session_context.update_test_variables("response", resp_obj)
            self.do_hook_actions(teardown_hooks, "teardown")

        # 断言
        validators = test_dict.get("validate", [])
        try:
            self.session_context.validate(validators, resp_obj)
        except (exceptions.ParamsError, exceptions.ValidationFailure, exceptions.ExtractFailure):

            err_msg = f"""\n
            {"*" * 32, "*" * 32} 请求响应详细信息 {"*" * 32, "*" * 32}\n
            ====== 请求详细信息 ======\n
            url: {url}\n
            method: {method}\n
            headers: {parsed_test_request.pop("headers", {})}\n
            
            ====== 响应详细信息 ======\n"
            status_code: {resp_obj.status_code}\n
            headers: {resp_obj.headers}\n
            body: {repr(resp_obj.text)}\n
            """
            logger.log_error(err_msg)

            raise

        finally:
            self.validation_results = self.session_context.validation_results

    def _run_testcase(self, testcase_dict):
        """ 运行单个testcase """
        self.meta_datas = []
        config = testcase_dict.get("config", {})

        # each teststeps in one testcase (YAML/JSON) share the same session.
        test_runner = Runner(config, self.functions, self.http_client_session)

        tests = testcase_dict.get("teststeps", [])
        for index, test_dict in enumerate(tests):

            # override current teststep variables with former testcase output variables
            former_output_variables = self.session_context.test_variables_mapping
            if former_output_variables:
                test_dict.setdefault("variables", {})
                test_dict["variables"].update(former_output_variables)

            try:
                test_runner.run_test(test_dict)
            except Exception:
                # log exception request_type and name for locust stat
                self.exception_request_type = test_runner.exception_request_type
                self.exception_name = test_runner.exception_name
                raise
            finally:
                _meta_datas = test_runner.meta_datas
                self.meta_datas.append(_meta_datas)

        self.session_context.update_session_variables(
            test_runner.extract_output(test_runner.output)
        )

    def run_test(self, test_dict):
        """ 运行testcase的单个测试步骤。test_dict可以有3种类型。
        Args:
            test_dict (dict):
                # teststep
                {
                    "name": "teststep description",
                    "variables": [],        # optional
                    "request": {
                        "url": "http://127.0.0.1:5000/api/users/1000",
                        "method": "GET"
                    }
                }

                # nested testcase
                {
                    "config": {...},
                    "teststeps": [
                        {...},
                        {...}
                    ]
                }

                # TODO: function
                {
                    "name": "exec function",
                    "function": "${func()}"
                }

        """
        self.meta_datas = None
        if "teststeps" in test_dict:
            # nested testcase
            self._run_testcase(test_dict)
        else:
            # api
            try:
                self._run_test(test_dict)
            except Exception:
                # log exception request_type and name for locust stat
                self.exception_request_type = test_dict["request"]["method"]
                self.exception_name = test_dict.get("name")
                raise
            finally:
                self.meta_datas = self.__get_test_data()

    def extract_output(self, output_variables_list):
        """ 从变量映射中提取变量并替换 """
        variables_mapping = self.session_context.session_variables_mapping

        output = {}
        for variable in output_variables_list:
            if variable not in variables_mapping:
                logger.log_warning(f"变量 '{variable}' 在变量映射中未找到, 替换失败")
                continue

            output[variable] = variables_mapping[variable]

        utils.print_info(output)
        return output
