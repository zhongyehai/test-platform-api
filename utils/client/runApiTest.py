# -*- coding: utf-8 -*-
import copy

from app.api_test.models.caseSet import ApiCaseSet as CaseSet
from app.api_test.models.api import ApiMsg as Api
from app.api_test.models.step import ApiStep as Step
from utils.log import logger
from utils.client.parseModel import StepModel
from utils.client.runTestRunner import RunTestRunner


class RunApi(RunTestRunner):
    """ 接口调试 """

    def __init__(
            self, project_id=None, run_name=None, api_ids=None, report_id=None, task=None, env_code=None, run_type="api"
    ):
        super().__init__(project_id=project_id, name=run_name, report_id=report_id, env_code=env_code, run_type=run_type)

        self.task = task
        self.api_ids = api_ids  # 要执行的接口id
        self.project = self.get_format_project(self.project_id)  # 解析当前服务信息
        self.format_data_for_template()  # 解析api
        self.count_step = 1
        self.report_model.parse_data_finish(self.report_id)

    def format_data_for_template(self):
        """ 接口调试 """
        logger.info(f'本次测试的接口id：\n{self.api_ids}')

        # 解析api
        for api_obj in self.api_ids:
            api = self.get_format_api(self.project, api_obj)

            # 用例的数据结构
            test_case_template = {
                "config": {
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
            case_id=[],
            task={},
            report_id=None,
            is_async=0,
            env_code="test",
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
            trigger_type=trigger_type,
            is_rollback=is_rollback,
            run_type=run_type,
            extend=extend
        )

        self.task = task
        self.DataTemplate["is_async"] = is_async
        self.case_id_list = case_id  # 要执行的用例id_list
        self.all_case_steps = []  # 所有测试步骤
        self.parse_all_case()
        self.report_model.parse_data_finish(self.report_id)

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

        return {
            "case_id": step.case_id,
            "name": step.name,
            "setup_hooks": [up.strip() for up in step.up_func.split(";") if up] if step.up_func else [],
            "teardown_hooks": [func.strip() for func in step.down_func.split(";") if func] if step.down_func else [],
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

            # 满足跳过条件则跳过
            if self.parse_case_is_skip(current_case.skip_if) is True:
                continue

            current_project = self.get_format_project(CaseSet.get_first(id=current_case.set_id).project_id)

            # 用例格式模板
            case_template = {
                "config": {
                    "run_type": self.run_type,
                    "variables": {},
                    "headers": {},
                    "name": current_case.name,
                    "run_env": self.env_code
                },
                "teststeps": []
            }

            # 递归获取测试步骤（中间有可能某些测试步骤是引用的用例）
            self.get_all_steps(case_id)
            print(f'最后解析出的步骤为：{self.all_case_steps}')

            # 循环解析测试步骤
            all_variables = {}  # 当前用例的所有公共变量
            for step in self.all_case_steps:
                step = StepModel(**step.to_dict())
                case = self.get_format_case(step.case_id)
                api_temp = Api.get_first(id=step.api_id)
                project = self.get_format_project(api_temp.project_id)
                api = self.get_format_api(project, api_temp)

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
                        case_template["teststeps"].append(
                            self.parse_step(current_project, project, current_case, case, api, step))
                else:
                    case_template["teststeps"].append(
                        self.parse_step(current_project, project, current_case, case, api, step))

                # 把服务和用例的的自定义变量留下来
                all_variables.update(project.variables)
                all_variables.update(case.variables)

            # 更新当前服务+当前用例的自定义变量，最后以当前用例设置的自定义变量为准
            all_variables.update(current_project.variables)
            all_variables.update(current_case.variables)
            case_template["config"]["variables"].update(all_variables)  # = all_variables

            # 设置的用例执行多少次就加入多少次
            name = case_template["config"]["name"]
            for index in range(current_case.run_times or 1):
                case_template["config"]["name"] = f'{name}_{index + 1}' if current_case.run_times > 1 else name
                # self.DataTemplate["testcases"].append(copy.copy(case_template))
                self.DataTemplate["testcases"].append(copy.deepcopy(case_template))

            # 完整的解析完一条用例后，去除对应的解析信息
            self.all_case_steps = []

        # 去除服务级的公共变量，保证用步骤上解析后的公共变量
        self.DataTemplate["project_mapping"]["variables"] = {}
