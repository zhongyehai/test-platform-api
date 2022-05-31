# encoding: utf-8
import copy
from unittest.case import SkipTest

# from . import exceptions, logger, response, utils
from . import exceptions, logger, utils
from .client import WebDriverSession
from .context import SessionContext
from .webdriverAction import Driver
from . import extract


class Runner(object):
    """ 运行测试用例

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

    def __init__(self, config: dict, functions, web_driver_client_session=None):
        """ 运行测试用例或者用例集

        Args:
            config (dict): testcase/testsuite config dict

                {
                    "name": "ABC",
                    "variables": {},
                    "setup_hooks", [],
                    "teardown_hooks", []
                }

            web_driver_client_session (instance): requests.Session(), or locust.client.Session() instance.

        """
        self.functions = functions
        self.validation_results = []

        testcase_setup_hooks = config.get("setup_hooks", [])  # 测试用例的前置操作

        self.testcase_teardown_hooks = config.get("teardown_hooks", [])  # 测试用例的后置操作

        self.web_driver_client_session = WebDriverSession()

        # 每一次执行用例时会先实例化Runner，此时实例化driver
        self.driver = Driver(config.get('browser_path'), config.get('browser_type'), config.get('web_driver_time_out'))

        self.session_context = SessionContext(self.functions)

        if testcase_setup_hooks:
            self.do_hook_actions(testcase_setup_hooks, "setup")

    def __del__(self):
        if self.testcase_teardown_hooks:
            self.do_hook_actions(self.testcase_teardown_hooks, "teardown")

    def __clear_test_data(self):
        """ 清除请求和响应数据 """
        self.validation_results = []

    def __get_test_data(self):
        """ get request/response data and validate results """
        # if not isinstance(self.web_driver_client_session, HttpSession):
        #     return

        meta_data = self.web_driver_client_session.meta_data
        meta_data["validators"] = self.validation_results
        return meta_data

    def _handle_skip_feature(self, step: dict):
        """ 根据动态条件判断是否跳过步骤
            - skip: 跳过当前步骤
            - skipIf: 值为true则跳过当前步骤
            - skipUnless: 除非条件为true，否则跳过当前步骤

        Args:
            step：步骤字典

        Raises:
            跳过当前步骤异常

        """

        if "skip" in step and step["skip"]:
            raise SkipTest(f'根据 skip 字段，{step["skip"]}，跳过当步骤')

        elif "skipIf" in step:
            skip_if_condition = step["skipIf"]
            if self.session_context.eval_content(skip_if_condition):
                raise SkipTest(f'根据 skipIf 字段，{skip_if_condition} 为 True，跳过当步骤')

        elif "skipUnless" in step:
            skip_unless_condition = step["skipUnless"]
            if not self.session_context.eval_content(skip_unless_condition):
                raise SkipTest(f'根据 skipUnless 字段，{skip_unless_condition} 为 False，跳过当步骤')

    def do_hook_actions(self, actions: list, hook_type: str):
        """ 执行前置/后置自定义函数
        Args:
            actions (list):
                format1 (dict): 执行自定义函数，并把自定义函数返回的值赋予给key，{"var": "${func()}"}
                format2 (str): 只执行自定义函数，${func()}

            hook_type (enum): setup/teardown
        """
        logger.log_debug(f"执行 {hook_type} 类型函数")
        for action in actions:

            if isinstance(action, dict) and len(action) == 1:  # format1
                var_name, hook_content = list(action.items())[0]
                hook_content_eval = self.session_context.eval_content(hook_content)
                logger.log_debug(f"assignment with hook: {var_name} = {hook_content} => {hook_content_eval}")
                self.session_context.update_test_variables(var_name, hook_content_eval)
            else:  # format 2
                logger.log_debug(f"执行自定义函数 {action}")
                # TODO: check hook function if valid
                self.session_context.eval_content(action)

    def _run_test(self, step_dict):
        """ 单个teststep运行。

        Args:
            step_dict (dict): teststep info
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
        self.__clear_test_data()  # 清除内存中的测试数据
        # print(test_dict)
        # prepare
        # test_dict = utils.lower_test_dict_keys(test_dict)
        test_variables = step_dict.get("variables", {})
        self.session_context.init_test_variables(test_variables)

        # 是否跳过当前步骤
        if step_dict.get('skipIf'):
            step_dict['skipIf'] = self.session_context.eval_content(step_dict.get('skipIf'))
        self._handle_skip_feature(step_dict)

        # 步骤名
        test_name = step_dict.get("name", "")

        # 解析请求，替换变量、自定义函数
        test_action = step_dict.get('test_action', {})
        parsed_step = self.session_context.eval_content(test_action)
        self.session_context.update_test_variables("request", parsed_step)

        # 执行前置函数
        setup_hooks = step_dict.get("setup_hooks", [])
        if setup_hooks:
            self.do_hook_actions(setup_hooks, "setup")

        # 深拷贝除 request 的其他数据，请求数据有可能是io，io不能深拷贝，所以先移出再深拷贝，再移入
        request = self.session_context.test_variables_mapping.pop('request')
        variables_mapping = copy.deepcopy(self.session_context.test_variables_mapping)
        self.session_context.test_variables_mapping['request'] = request

        # 执行测试步骤浏览器操作
        self.web_driver_client_session.do_action(
            self.driver,
            test_name,
            variables_mapping=copy.deepcopy(variables_mapping),
            **parsed_step
        )

        # 数据提取
        extractors = step_dict.get("extract", {})
        extracted_variables_mapping = extract.extract_data(self.session_context, self.driver, extractors)
        self.web_driver_client_session.meta_data['data'][0]['extract_msgs'] = extracted_variables_mapping
        self.session_context.update_session_variables(extracted_variables_mapping)

        # 后置函数
        teardown_hooks = step_dict.get("teardown_hooks", [])
        if teardown_hooks:
            # self.session_context.update_test_variables("response", resp_obj)
            self.do_hook_actions(teardown_hooks, "teardown")

        # 断言
        try:
            self.session_context.validate(step_dict.get("validate", []), self.driver)
        except (exceptions.ParamsError, exceptions.ValidationFailure, exceptions.ExtractFailure):

            # err_msg = f"""\n
            # {"*" * 32, "*" * 32} 请求响应详细信息 {"*" * 32, "*" * 32}\n
            # ====== 请求详细信息 ======\n
            # url: {url}\n
            # method: {method}\n
            # headers: {parsed_step.pop("headers", {})}\n
            #
            # ====== 响应详细信息 ======\n"
            # status_code: {resp_obj.status_code}\n
            # headers: {resp_obj.headers}\n
            # body: {repr(resp_obj.text)}\n
            # """
            # logger.log_error(err_msg)

            raise

        finally:
            self.validation_results = self.session_context.validation_results

    def _run_testcase(self, testcase_dict):
        """ 运行单个testcase """
        self.meta_datas = []
        config = testcase_dict.get("config", {})

        # each teststeps in one testcase (YAML/JSON) share the same session.
        test_runner = Runner(config, self.functions, self.web_driver_client_session)

        step_list = testcase_dict.get("teststeps", [])
        for index, test_dict in enumerate(step_list):

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

    def run_test(self, step: dict):
        """ 运行testcase的单个测试步骤。test_dict可以有3种类型。
        Args:
        {
            "config": {
                "browser_type": "chrome",
                "browser_path": r"D:\drivers\chromedriver.exe",
                "name": "任务测试01",
                "variables": {
                    "AAtoken": "eyJhbGciOiJIUzUxMiJ9"
                }
            },
            "teststeps": [
                {
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
                }
            ]
        }

        """
        self.meta_datas = None
        if "teststeps" in step:
            # nested testcase
            self._run_testcase(step)
        else:
            # api
            try:
                self._run_test(step)
            except Exception:
                # log exception request_type and name for locust stat
                # self.exception_request_type = test_dict["request"]["method"]
                # self.exception_name = test_dict.get("name")
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
