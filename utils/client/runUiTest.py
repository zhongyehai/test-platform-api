# -*- coding: utf-8 -*-
import copy
import json

from utils.client.runTestRunner import RunTestRunner
from utils.util.fileUtil import FileUtil
from utils.client.parseModel import StepModel, FormatModel
from utils.client.testRunner.utils import build_url
from app.web_ui_test.models.caseSuite import WebUiCaseSuite
from app.web_ui_test.models.step import WebUiStep
from app.web_ui_test.models.report import WebUiReportStep
from app.app_ui_test.models.caseSuite import AppUiCaseSuite
from app.app_ui_test.models.step import AppUiStep
from app.app_ui_test.models.report import AppUiReportStep
from app.app_ui_test.models.device import AppUiRunPhone
from config import ui_action_mapping_reverse


class RunCase(RunTestRunner):
    """ 运行测试用例 """

    def __init__(
            self,
            project_id=None,
            run_name=None,
            temp_variables=None,
            case_id=[],
            task={},
            report_id=None,
            is_async=True,
            browser=True,
            env_code="test",
            env_name=None,
            trigger_type="page",
            is_rollback=False,
            appium_config={},
            run_type="web_ui",
            extend={},
            **kwargs
    ):
        super(RunCase, self).__init__(
            project_id=project_id,
            name=run_name,
            report_id=report_id,
            env_code=env_code,
            env_name=env_name,
            trigger_type=trigger_type,
            is_rollback=is_rollback,
            run_type=run_type,
            extend=extend
        )
        self.temp_variables = temp_variables
        self.task = task
        self.run_type = run_type
        if run_type == "webUi":
            self.suite_model = WebUiCaseSuite
            self.step_model = WebUiStep
            self.reportStepModel = WebUiReportStep
            self.browser = browser
            self.device = self.device_id = self.run_server_id = self.run_phone_id = None
            self.device_dict = {}
        else:
            self.suite_model = AppUiCaseSuite
            self.step_model = AppUiStep
            self.reportStepModel = AppUiReportStep
            self.run_server_id = appium_config.pop("server_id")
            self.run_phone_id = appium_config.pop("phone_id")
            self.device = appium_config.pop("device")
            self.device_id = self.device["device_id"]
            self.device_dict = {device.id: device.to_dict() for device in AppUiRunPhone.get_all()}

        self.DataTemplate["is_async"] = is_async
        self.case_id_list = case_id  # 要执行的用例id_list
        self.appium_config = appium_config
        self.all_case_steps = []  # 所有测试步骤
        self.parse_all_case()
        self.report_model.parse_data_finish(self.report_id)

    def parse_step(self, project, element, step):
        """ 解析测试步骤
        project: 当前步骤对应元素所在的项目(解析后的)
        element: 解析后的element
        step: 原始step
        返回解析后的步骤 {}
        """
        step_data = {
            "case_id": step.case_id,
            "name": step.name,
            "setup_hooks": [up.strip() for up in step.up_func.split(";") if up] if step.up_func else [],
            "teardown_hooks": [func.strip() for func in step.down_func.split(";") if func] if step.down_func else [],
            "skip": not step.status,  # 无条件跳过当前测试
            "skipIf": step.skip_if,  # 如果条件为真，则跳过当前测试
            # "skipUnless": "",  # 除非条件为真，否则跳过当前测试
            "times": step.run_times,  # 运行次数
            "extract": step.extracts,  # 要提取的信息
            "validate": step.validates,  # 断言信息
            "test_action": {
                "execute_name": step.execute_name,
                "action": step.execute_type,
                "by_type": element.by,
                "screen": None if self.run_type == 'webUi' else self.device_dict[element.template_device]["screen"],
                # 如果是打开页面，则设置为项目域名+页面地址
                "element": build_url(project.host, element.element) if element.by == "url" else element.element,
                "text": step.send_keys,
                "wait_time_out": float(step.wait_time_out or element.wait_time_out or self.wait_time_out)
            }
        }

        report_step = self.reportStepModel().create({
            "name": step_data["name"],
            "from_id": element.id,
            "step_id": step.id,
            "step_data": step_data,
            "report_id": self.report_id,
        })

        step_data["report_step_id"] = report_step.id
        return step_data


    def parse_extracts(self, extracts: list):
        """ 解析数据提取
        extracts_list:
            [
                {"data_source": "extract_09_value", "key": "name1", "remark": None, "value": 1},
                {"data_source": "func", "key": "name2", "remark": None, "value": "$do_something()"},
            ]
        return:
            [
                {
                    "type": "element",
                    "key": "name1",
                    "value": {
                        "action": "action_09get_value",
                        "by_type": "id",
                        "element": "su"
                    }
                },
                {"type": "func", "key": "name2", "value": "$do_something()"},
            ]
        """
        parsed_list = []
        for extract in extracts:
            if extract["extract_type"] in ("const", "func", "variable"):  # 自定义函数、变量提取、常量
                parsed_list.append({
                    "type": extract["extract_type"],
                    "key": extract.get("key"),
                    "value": extract.get("value")
                })
            elif extract["extract_type"]:  # 页面元素提取
                element = self.get_format_element(extract["value"])
                parsed_list.append({
                    "type": "element",
                    "key": extract.get("key"),
                    "value": {
                        "action": extract.get("extract_type"),
                        "by_type": element.by,
                        "element": element.element
                    }
                })
        return parsed_list

    def parse_validates(self, validates_list):
        """ 解析断言
        validates:
                [
                    {
                        '_01equals': ['variable.$a', '123']
                    },
                    {
                        'id': '1686479480568',
                        'validate_type': 'page',
                        'data_source': 3,
                        'key': None,
                        'validate_method': '相等',
                        'data_type': 'str',
                        'value': '234'
                    }
                ]
        return:
            [
                {          {
                    '_01equals': ['variable.$a', '123']
                },
                {
                    "comparator": "validate_type",  # 断言方式
                    "check": ("id", "kw"),  # 实际结果
                    "expect": "123123"  # 预期结果
                }
            ]
        """
        parsed_validate = []
        for validate in validates_list:
            if validate.get("data_source"):  # 页面断言，需要解析ui元素
                element = self.get_format_element(validate["data_source"])
                parsed_validate.append({
                    "comparator": validate["validate_method"],  # 断言方式
                    "check": (element.by, element.element),  # 实际结果
                    "expect": self.build_expect_result(validate["data_type"], validate["value"])  # 预期结果
                })
            else:
                parsed_validate.append(validate)  # 已经解析过的数据断言
        return parsed_validate

    def build_expect_result(self, data_type, value):
        """ 生成预期结果 """
        if data_type in ["variable", "func", "str"]:
            return value
        elif data_type == "json":
            return json.dumps(json.loads(value))
        else:  # python数据类型
            return eval(f'{data_type}({value})')

    def get_all_steps(self, case_id: int):
        """ 解析引用的用例 """
        case = self.get_format_case(case_id)

        # 不满足跳过条件才解析
        if self.parse_case_is_skip(case.skip_if, self.run_server_id, self.run_phone_id) is not True:
            steps = self.step_model.query.filter_by(case_id=case.id, status=1).order_by(self.step_model.num.asc()).all()
            for step in steps:
                if step.quote_case:
                    self.get_all_steps(step.quote_case)
                else:
                    self.all_case_steps.append(step)
                    self.count_step += 1
                    self.element_set.add(step.element_id)

    def parse_all_case(self):
        """ 解析所有用例 """

        # 遍历要运行的用例
        for case_id in self.case_id_list:

            current_case = self.get_format_case(case_id)
            if current_case is None:
                continue

            if self.temp_variables:
                current_case.variables = FormatModel().parse_variables(self.temp_variables.get("variables"))
                current_case.skip_if = FormatModel().parse_skip_if(self.temp_variables.get("skip_if"))
                current_case.run_times = self.temp_variables.get("run_times", 1)

            # 满足跳过条件则跳过
            if self.parse_case_is_skip(current_case.skip_if, self.run_server_id, self.run_phone_id) is True:
                continue

            current_project = self.get_format_project(self.suite_model.get_first(id=current_case.suite_id).project_id)

            case_template = {
                "config": {
                    "case_id": case_id,
                    "project_id": current_project.id,
                    "variables": {},
                    "name": current_case.name,
                    "run_type": self.run_type
                },
                "teststeps": []
            }
            if self.run_type == 'webUi':
                # 用例格式模板, # 火狐：geckodriver
                case_template["config"]["browser_type"] = self.browser
                case_template["config"]["browser_path"] = FileUtil.get_driver_path(self.browser)
            else:
                case_template["config"]["appium_config"] = self.appium_config

            self.get_all_steps(case_id)  # 递归获取测试步骤（中间有可能某些测试步骤是引用的用例）

            # 循环解析测试步骤
            all_variables = {}  # 当前用例的所有公共变量
            for step in self.all_case_steps:
                step_case = self.get_format_case(step.case_id)
                step_element = self.get_format_element(step.element_id)
                step = StepModel(**step.to_dict())
                step.execute_name = ui_action_mapping_reverse[step.execute_type]  # 执行方式的别名，用于展示测试报告
                step.extracts = self.parse_extracts(step.extracts)  # 解析数据提取
                step.validates = self.parse_validates(step.validates)  # 解析断言
                element_project = self.get_format_project(step_element.project_id)  # 元素所在的项目

                if step.data_driver:  # 如果有step.data_driver，则说明是数据驱动
                    """
                    数据驱动格式
                    [
                        {"comment": "用例1描述", "data": "请求数据，支持参数化"},
                        {"comment": "用例2描述", "data": "请求数据，支持参数化"}
                    ]
                    """
                    for driver_data in step.data_driver:
                        # 数据驱动的 comment 字段，用于做标识
                        step.name += driver_data.get("comment", "")
                        step.params = step.params = step.data_json = step.data_form = driver_data.get("data", {})
                        case_template["teststeps"].append(self.parse_step(element_project, step_element, step))
                else:
                    case_template["teststeps"].append(self.parse_step(element_project, step_element, step))

                # 把服务和用例的的自定义变量留下来
                all_variables.update(element_project.variables)
                all_variables.update(step_case.variables)

            # 更新当前服务+当前用例的自定义变量，最后以当前用例设置的自定义变量为准
            all_variables.update(current_project.variables)
            all_variables.update(current_case.variables)
            all_variables.update({"device": self.device})  # 强制增加一个变量为设备id，用于去数据库查数据
            all_variables.update({"device_id": self.device_id})  # 强制增加一个变量为设备id，用于去数据库查数据
            case_template["config"]["variables"].update(all_variables)

            # 设置的用例执行多少次就加入多少次
            name = case_template["config"]["name"]
            for index in range(current_case.run_times or 1):
                case_template["config"]["name"] = f'{name}_{index + 1}' if current_case.run_times > 1 else name
                self.DataTemplate["testcases"].append(copy.deepcopy(case_template))

            # 完整的解析完一条用例后，去除对应的解析信息
            self.all_case_steps = []

        # 去除服务级的公共变量，保证用步骤上解析后的公共变量
        self.DataTemplate["project_mapping"]["variables"] = {}
