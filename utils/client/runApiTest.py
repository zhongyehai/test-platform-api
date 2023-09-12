# -*- coding: utf-8 -*-
import copy

from app.api_test.models.caseSuite import ApiCaseSuite as CaseSuite
from app.api_test.models.api import ApiMsg as Api
from app.api_test.models.step import ApiStep as Step
from app.api_test.models.report import ApiReportCase as ReportCase, ApiReportStep as reportStep
from utils.log import logger
from utils.client.parseModel import StepModel, FormatModel
from utils.client.runTestRunner import RunTestRunner


class RunApi(RunTestRunner):
    """ 接口调试 """

    def __init__(
            self, project_id=None, run_name=None, api_ids=None, report_id=None, task=None, env_code=None, env_name=None,
            run_type="api"
    ):
        super().__init__(
            project_id=project_id, name=run_name, report_id=report_id, env_code=env_code, env_name=env_name,
            run_type=run_type
        )

        self.task = task
        self.api_ids = api_ids  # 要执行的接口id
        self.project = {}  # 解析当前服务信息
        self.project = self.get_format_project(self.project_id)  # 解析当前服务信息
        self.format_data_for_template()  # 解析api
        self.count_step = 1
        self.report_model.parse_data_finish(self.report_id)

    def parse_and_run(self):
        """ 把解析放到异步线程里面 """
        self.run_case()

    def format_data_for_template(self):
        """ 接口调试 """
        logger.info(f'本次测试的接口id：\n{self.api_ids}')

        # 解析api
        for api_obj in self.api_ids:
            api = self.get_format_api(self.project, api_obj)

            # 记录解析下后的用例，单接口运行时，没有用例，为了统一数据结构，所以把接口视为一条用例
            report_case = ReportCase().create({
                "name": api["name"],
                "from_id": api["id"],
                "report_id": self.report_id,
                "case_data": api,
            })

            # 用例的数据结构
            test_case_template = {
                "config": {
                    "report_case_id": report_case.id,
                    "run_type": self.run_type,
                    "name": api.get("name"),
                    "variables": {},
                    "setup_hooks": [],
                    "teardown_hooks": []
                },
                "teststeps": []  # 测试步骤
            }

            # 合并头部信息
            headers = {}
            headers.update(self.project.headers)
            headers.update(api["request"]["headers"])
            api["request"]["headers"] = headers

            report_step = reportStep().create({
                "name": api["name"],
                "from_id": api["id"],
                "step_data": api,
                "report_id": self.report_id,
                "report_case_id": report_case.id,
            })
            api["report_step_id"] = report_step.id

            # 把api加入到步骤
            test_case_template["teststeps"].append(api)

            # 更新公共变量
            test_case_template["config"]["variables"].update(self.project.variables)
            self.DataTemplate["testcases"].append(copy.deepcopy(test_case_template))


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
            is_async=0,
            env_code="test",
            env_name=None,
            trigger_type="page",
            is_rollback=False,
            run_type="api",
            extend={},
            **kwargs
    ):
        super().__init__(
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
        self.DataTemplate["is_async"] = is_async
        self.case_id_list = case_id  # 要执行的用例id_list
        self.all_case_steps = []  # 所有测试步骤

    def parse_and_run(self):
        """ 把解析放到异步线程里面 """
        self.parse_all_case()
        self.report_model.parse_data_finish(self.report_id)
        self.run_case()

    def parse_step(self, current_project, project, current_case, case, api, step):
        """ 解析测试步骤
        current_project: 当前用例所在的服务(解析后的)
        project: 当前步骤对应接口所在的服务(解析后的)
        current_case: 当前用例
        case: 被引用的case
        api: 解析后的api
        step: 原始step
        返回解析后的步骤 {}
        """
        # 解析头部信息，继承头部信息，接口所在服务、当前所在服务、用例、步骤
        headers = {}
        headers.update(project.headers)
        if case:
            headers.update(case.headers)
        headers.update(current_project.headers)
        # headers.update(api["request"]["headers"])
        headers.update(current_case.headers)
        headers.update(step.headers)

        # 如果步骤设置了不使用字段，则去掉
        for filed in step.pop_header_filed:
            if filed in headers:
                headers.pop(filed)

        step_data = {
            "case_id": step.case_id,
            "name": step.name,
            "setup_hooks": step.up_func,
            "teardown_hooks": step.down_func,
            "skip": not step.status,  # 直接指定当前步骤是否执行
            "skipIf": step.skip_if,  # 如果条件为真，则当前步骤不执行
            # "skipUnless": "",  # 除非条件为真，否则跳过当前测试
            "times": step.run_times,  # 运行次数
            "extract": step.extracts,  # 接口要提取的信息
            "validate": step.validates,  # 接口断言信息
            "base_url": current_project.host if step.replace_host == 1 else project.host,
            "request": {
                "method": api["request"]["method"],
                "url": api["request"]["url"],
                "timeout": step.time_out or api["request"]["timeout"] or self.time_out,
                "headers": headers,  # 接口头部信息
                "params": step.params,  # 接口查询字符串参数
                "json": step.data_json,
                "data": step.data_form,
                "files": step.data_file,
            }
        }
        report_step = reportStep().create({
            "name": step_data["name"],
            "from_id": api["id"],
            "case_id": step.case_id,
            "step_id": step.id,
            "step_data": step_data,
            "report_id": self.report_id,
            "report_case_id": current_case.report_case_id
        })
        step_data["report_step_id"] = report_step.id
        return step_data

    def get_all_steps(self, case_id: int):
        """ 解析引用的用例 """
        case = self.get_format_case(case_id)

        if self.parse_case_is_skip(case.skip_if) is not True:  # 不满足跳过条件才解析
            steps = Step.query.filter_by(case_id=case.id, status=1).order_by(Step.num.asc()).all()
            for step in steps:
                if step.quote_case:
                    self.get_all_steps(step.quote_case)
                else:
                    self.all_case_steps.append(step)
                    self.count_step += 1
                    self.api_set.add(step.api_id)

    def parse_all_case(self):
        """ 解析所有用例 """

        # 遍历要运行的用例
        for case_id in self.case_id_list:

            current_case = self.get_format_case(case_id)
            if current_case is None:
                continue

            # 如果传了临时参数
            if self.temp_variables:
                current_case.variables = FormatModel().parse_variables(self.temp_variables.get("variables"))
                current_case.headers = FormatModel().parse_list_data(self.temp_variables.get("headers"))
                current_case.skip_if = FormatModel().parse_skip_if(self.temp_variables.get("skip_if"))
                current_case.run_times = self.temp_variables.get("run_times", 1)

            for index in range(current_case.run_times or 1):
                case_name = f'{current_case.name}_{index + 1}' if current_case.run_times > 1 else current_case.name

                # 记录解析下后的用例
                report_case = ReportCase().create({
                    "name": case_name,
                    "from_id": current_case.id,
                    "report_id": self.report_id,
                    "case_data": current_case.get_attr(),
                    "summary": ReportCase.get_summary_template()
                })
                current_case.report_case_id = report_case.id

                # 满足跳过条件则跳过
                if self.parse_case_is_skip(current_case.skip_if) is True:
                    report_case.test_is_skip()
                    continue

                current_project = self.get_format_project(CaseSuite.get_first(id=current_case.suite_id).project_id)

                # 用例格式模板
                case_template = {
                    "config": {
                        "report_case_id": report_case.id,
                        "case_id": case_id,
                        "project_id": current_project.id,
                        "run_type": self.run_type,
                        "variables": {},
                        "headers": {},
                        "name": case_name,
                        "run_env": self.env_code
                    },
                    "teststeps": []
                }

                self.get_all_steps(case_id)  # 递归获取测试步骤（中间有可能某些测试步骤是引用的用例）

                # 循环解析测试步骤
                all_variables = {}  # 当前用例的所有公共变量
                for step in self.all_case_steps:
                    step = StepModel(**step.to_dict())
                    step_case = self.get_format_case(step.case_id)
                    api_temp = Api.get_first(id=step.api_id)
                    api_project = self.get_format_project(api_temp.project_id)
                    api = self.get_format_api(api_project, api_temp)

                    if step.data_driver:  # 如果有step.data_driver，则说明是数据驱动， 此功能废弃
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
                            case_template["teststeps"].append(
                                self.parse_step(current_project, api_project, current_case, step_case, api, step))
                    else:
                        case_template["teststeps"].append(
                            self.parse_step(current_project, api_project, current_case, step_case, api, step))

                    # 把服务和用例的的自定义变量留下来
                    all_variables.update(api_project.variables)
                    all_variables.update(step_case.variables)

                # 更新当前服务+当前用例的自定义变量，最后以当前用例设置的自定义变量为准
                all_variables.update(current_project.variables)
                all_variables.update(current_case.variables)
                case_template["config"]["variables"].update(all_variables)  # = all_variables

                self.DataTemplate["testcases"].append(copy.deepcopy(case_template))

                # 完整的解析完一条用例后，去除对应的解析信息
                self.all_case_steps = []

        # 去除服务级的公共变量，保证用步骤上解析后的公共变量
        self.DataTemplate["project_mapping"]["variables"] = {}
