# -*- coding: utf-8 -*-
import json
import types
import importlib
from threading import Thread
from datetime import datetime

from flask.json import JSONEncoder

from app.api_test.models.caseSuite import ApiCaseSuite
from app.api_test.models.api import ApiMsg
from app.api_test.models.case import ApiCase
from app.api_test.models.step import ApiStep
from app.api_test.models.project import ApiProject, ApiProjectEnv, db
from app.api_test.models.report import ApiReport
from app.web_ui_test.models.project import WebUiProject, WebUiProjectEnv
from app.web_ui_test.models.element import WebUiElement
from app.web_ui_test.models.caseSuite import WebUiCaseSuite
from app.web_ui_test.models.case import WebUiCase
from app.web_ui_test.models.step import WebUiStep
from app.web_ui_test.models.report import WebUiReport
from app.app_ui_test.models.project import AppUiProject, AppUiProjectEnv
from app.app_ui_test.models.element import AppUiElement
from app.app_ui_test.models.caseSuite import AppUiCaseSuite
from app.app_ui_test.models.case import AppUiCase
from app.app_ui_test.models.step import AppUiStep
from app.app_ui_test.models.report import AppUiReport
from app.config.models.runEnv import RunEnv

from app.assist.models.script import Script
from app.config.models.config import Config
from utils.client.testRunner.api import TestRunner
from utils.client.testRunner.utils import build_url
from utils.log import logger
from utils.parse.parse import encode_object
from utils.client.parseModel import ProjectModel, ApiModel, CaseModel, ElementModel
from utils.message.sendReport import async_send_report, call_back_for_pipeline
from utils.client.testRunner import built_in


class RunTestRunner:

    def __init__(
            self,
            project_id=None,
            name=None,
            report_id=None,
            env_code=None,
            env_name=None,
            trigger_type="page",
            is_rollback=False,
            run_type="api",
            extend={}
    ):
        self.env_code = env_code  # 运行环境id
        self.env_name = env_name  # 运行环境名，用于发送即时通讯
        self.extend = extend
        self.project_id = project_id
        self.run_name = name
        self.is_rollback = is_rollback
        self.trigger_type = trigger_type
        self.time_out = Config.get_request_time_out()
        self.wait_time_out = Config.get_wait_time_out()
        self.run_type = run_type

        self.api_model = ApiMsg
        self.element_model = None
        if self.run_type == "api":  # 接口自动化
            self.project_model = ApiProject
            self.project_env_model = ApiProjectEnv
            self.suite_model = ApiCaseSuite
            self.case_model = ApiCase
            self.step_model = ApiStep
            self.report_model = ApiReport
            self.front_report_addr = f'{Config.get_report_host()}{Config.get_api_report_addr()}'
        elif self.run_type == "webUi":  # web-ui自动化
            self.project_model = WebUiProject
            self.project_env_model = WebUiProjectEnv
            self.element_model = WebUiElement
            self.suite_model = WebUiCaseSuite
            self.case_model = WebUiCase
            self.step_model = WebUiStep
            self.report_model = WebUiReport
            self.front_report_addr = f'{Config.get_report_host()}{Config.get_web_ui_report_addr()}'
        else:  # app-ui自动化
            self.project_model = AppUiProject
            self.project_env_model = AppUiProjectEnv
            self.element_model = AppUiElement
            self.suite_model = AppUiCaseSuite
            self.case_model = AppUiCase
            self.step_model = AppUiStep
            self.report_model = AppUiReport
            self.front_report_addr = f'{Config.get_report_host()}{Config.get_app_ui_report_addr()}'

        self.report_id = report_id
        self.parsed_project_dict = {}
        self.parsed_case_dict = {}
        self.parsed_api_dict = {}
        self.parsed_element_dict = {}

        self.count_step = 0
        self.api_set = set()
        self.element_set = set()

        self.run_env = RunEnv.get_first(code=self.env_code).to_dict()

        Script.create_script_file(self.env_code)  # 创建所有函数文件

        # testRunner需要的数据格式
        self.DataTemplate = {
            "is_async": 0,
            "project": self.run_name,
            "run_type": self.run_type,
            "project_mapping": {
                "functions": {},
                "variables": {}
            },
            "testsuites": [],  # 用例集
            "testcases": [],  # 用例
            "apis": [],  # 接口
        }

    def get_format_project(self, project_id):
        """ 从已解析的服务字典中取指定id的服务，如果没有，则取出来解析后放进去 """
        if project_id not in self.parsed_project_dict:
            project = self.project_model.get_first(id=project_id).to_dict()
            self.parse_functions(project["script_list"])
            project_env = self.project_env_model.get_first(
                env_id=self.run_env["id"], project_id=project["id"]).to_dict()
            project_env.update(project)
            project_env.update(self.run_env)
            self.parsed_project_dict.update({project_id: ProjectModel(**project_env)})
        return self.parsed_project_dict[project_id]

    def get_format_case(self, case_id):
        """ 从已解析的用例字典中取指定id的用例，如果没有，则取出来解析后放进去 """
        if case_id not in self.parsed_case_dict:
            case = self.case_model.get_first(id=case_id)
            if not case:
                return  # 可能存在任务选择了用例，在那边直接把这条用例删掉了的情况
            self.parse_functions(json.loads(case.script_list))
            self.parsed_case_dict.update({case_id: CaseModel(**case.to_dict())})
        return self.parsed_case_dict[case_id]

    def get_format_element(self, element_id):
        """ 从已解析的元素字典中取指定id的元素，如果没有，则取出来解析后放进去 """
        if element_id not in self.parsed_element_dict:
            element = self.element_model.get_first(id=element_id).to_dict()
            self.parsed_element_dict.update({element_id: ElementModel(**element)})
        return self.parsed_element_dict[element_id]

    def get_format_api(self, project, api):
        """ 从已解析的接口字典中取指定id的接口，如果没有，则取出来解析后放进去 """
        if api.id not in self.parsed_api_dict:
            if api.project_id not in self.parsed_project_dict:
                self.parse_functions(json.loads(self.project_model.get_first(id=api.project_id).script_list))
            self.parsed_api_dict.update({
                api.id: self.parse_api(project, ApiModel(**api.to_dict()))
            })
        return self.parsed_api_dict[api.id]

    def parse_functions(self, func_list):
        """ 获取自定义函数 """
        for func_file_id in func_list:
            func_file_name = Script.get_first(id=func_file_id).name
            func_file_data = importlib.reload(importlib.import_module(f'script_list.{self.env_code}_{func_file_name}'))
            self.DataTemplate["project_mapping"]["functions"].update({
                name: item for name, item in vars(func_file_data).items() if isinstance(item, types.FunctionType)
            })

    def parse_case_is_skip(self, skip_if_list, server_id=None, phone_id=None):
        """ 判断是否跳过用例，暂时只支持对运行环境的判断 """
        for skip_if in skip_if_list:
            skip_type = skip_if["skip_type"]
            if skip_if["data_source"] == "run_env":
                skip_if["check_value"] = self.env_code
            elif skip_if["data_source"] == "run_server":
                skip_if["check_value"] = server_id
            elif skip_if["data_source"] == "run_device":
                skip_if["check_value"] = phone_id
            try:
                comparator = getattr(built_in, skip_if["comparator"])
                skip_if_result = comparator(skip_if["check_value"], skip_if["expect"])  # 借用断言来判断条件是否为真
            except Exception as error:
                skip_if_result = error
            if ("true" in skip_type and not skip_if_result) or ("false" in skip_type and skip_if_result):
                return True

    def parse_ui_test_step(self, project, element, step):
        """ 解析 UI自动化测试步骤
        project: 当前步骤对应元素所在的项目(解析后的)
        element: 解析后的element
        step: 原始step
        返回解析后的步骤 {}
        """
        return {
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
                # 如果是打开页面，则设置为项目域名+页面地址
                "element": build_url(project.host, element.element) if element.by == "url" else element.element,
                "text": step.send_keys,
                "wait_time_out": float(step.wait_time_out or element.wait_time_out or self.wait_time_out)
            }
        }

    def save_report_and_send_message(self, json_result):
        """ 写入测试报告到数据库, 并把数据写入到文本中 """
        self.report_model.save_report_start(self.report_id)
        result = json.loads(json_result)

        report = self.report_model.get_first(id=self.report_id)
        report.update_status(result["success"])
        report.update({"summary": result})  # 保存测试报告概要数据
        self.report_model.save_report_finish(self.report_id)

        # 定时任务需要把连接放回连接池，不放回去会报错
        if self.is_rollback:
            db.session.rollback()

        # 有可能是多环境一次性批量运行，根据batch_id查是否全部运行完毕
        batch_id = self.report_model.get_first(id=self.report_id).batch_id  # 获取当前报告所属的batch_id
        if self.report_model.select_is_all_done_by_batch_id(batch_id):  # 查询此batch_id下的报告是否全部生成
            not_passed_report = self.report_model.get_first(batch_id=batch_id, is_passed=0)  # 有失败的，则获取失败的报告
            if not_passed_report:
                self.report_id = not_passed_report.id
                result = json.loads(self.report_model.get_first(id=not_passed_report.id).summary)

            self.send_report(self.report_id, result)  # 发送报告

    def run_case(self):
        """ 调 testRunner().run() 执行测试 """
        logger.info(f'请求数据：\n{self.DataTemplate}')

        if self.DataTemplate.get("is_async", 0):
            # 并行执行, 遍历case，以case为维度多线程执行，测试报告按顺序排列
            run_case_dict = {}
            self.report_model.run_case_start(self.report_id)
            for index, case in enumerate(self.DataTemplate["testcases"]):
                run_case_dict[index] = False  # 用例运行标识，索引：是否运行完成
                temp_case = self.DataTemplate
                temp_case["testcases"] = [case]
                self._async_run_case(temp_case, run_case_dict, index)
        else:  # 串行执行
            self.sync_run_case()

    def _run_case(self, case, run_case_dict, index):
        runner = TestRunner()
        runner.run(case)
        self.update_run_case_status(run_case_dict, index, runner.summary)

    def _async_run_case(self, case, run_case_dict, index):
        """ 多线程运行用例 """
        Thread(target=self._run_case, args=[case, run_case_dict, index]).start()

    def sync_run_case(self):
        """ 单线程运行用例 """
        self.report_model.run_case_start(self.report_id)
        runner = TestRunner()
        runner.run(self.DataTemplate)
        self.report_model.run_case_finish(self.report_id)
        summary = runner.summary
        summary["time"]["start_at"] = datetime.fromtimestamp(summary["time"]["start_at"]).strftime("%Y-%m-%d %H:%M:%S")
        summary["run_type"] = self.run_type
        summary["is_async"] = self.DataTemplate.get("is_async", 0)
        summary["run_env"] = self.env_code
        summary["env_name"] = self.env_name
        summary["count_step"] = self.count_step
        summary["count_api"] = len(self.api_set)
        summary["count_element"] = len(self.element_set)
        jump_res = json.dumps(summary, ensure_ascii=False, default=encode_object, cls=JSONEncoder)
        self.save_report_and_send_message(jump_res)

    def update_run_case_status(self, run_dict, run_index, summary):
        """ 每条用例执行完了都更新对应的运行状态，如果更新后的结果是用例全都运行了，则生成测试报告"""
        run_dict[run_index] = summary
        if all(run_dict.values()):  # 全都执行完毕
            self.report_model.run_case_finish(self.report_id)
            all_summary = run_dict[0]
            all_summary["run_type"] = self.run_type
            all_summary["is_async"] = self.DataTemplate.get("is_async", 0)
            all_summary["run_env"] = self.env_code
            all_summary["env_name"] = self.env_name
            all_summary["count_step"] = self.count_step
            all_summary["count_api"] = len(self.api_set)
            summary["count_element"] = len(self.element_set)
            all_summary["time"]["start_at"] = datetime.fromtimestamp(
                all_summary["time"]["start_at"]
            ).strftime("%Y-%m-%d %H:%M:%S")
            for index, res in enumerate(run_dict.values()):
                if index != 0:
                    self.build_summary(all_summary, res, ["testcases", "teststeps"])  # 合并用例统计, 步骤统计
                    all_summary["details"].extend(res["details"])  # 合并测试用例数据
                    all_summary["success"] = all([all_summary["success"], res["success"]])  # 测试报告状态
                    all_summary["time"]["duration"] = summary["time"]["duration"]  # 总共耗时取运行最长的

            jump_res = json.dumps(all_summary, ensure_ascii=False, default=encode_object, cls=JSONEncoder)
            self.save_report_and_send_message(jump_res)

    def send_report(self, report_id, res):
        """ 发送测试报告 """
        if self.task:
            # 如果是流水线触发的，则回调给流水线
            if self.trigger_type == "pipeline":
                call_back_for_pipeline(
                    self.task["id"],
                    self.task["call_back"] or [],
                    self.extend,
                    res["success"]
                )

            # 发送测试报告
            async_send_report(content=res, **self.task, report_id=report_id, report_addr=self.front_report_addr)

    @staticmethod
    def parse_api(project, api):
        """ 把解析后的接口对象 解析为testRunner的数据结构 """
        return {
            "id": api.id,
            "name": api.name,  # 接口名
            "setup_hooks": [up.strip() for up in api.up_func.split(";") if up] if api.up_func else [],
            "teardown_hooks": [func.strip() for func in api.down_func.split(";") if func] if api.down_func else [],
            "skip": "",  # 无条件跳过当前测试
            "skipIf": "",  # 如果条件为真，则跳过当前测试
            "skipUnless": "",  # 除非条件为真，否则跳过当前测试
            "times": 1,  # 运行次数
            "extract": api.extracts,  # 接口要提取的信息
            "validate": api.validates,  # 接口断言信息
            "base_url": project.host,
            "data_type": api.data_type,
            "variables": [],
            "request": {
                "method": api.method,
                "url": api.addr,
                "timeout": api.time_out,
                "headers": api.headers,  # 接口头部信息
                "params": api.params,  # 接口查询字符串参数
                "json": api.data_json,
                "data": api.data_form,
                "files": api.data_file
            }
        }

    @staticmethod
    def build_summary(source1, source2, fields):
        """ 合并测试报告统计 """
        for field in fields:
            for key in source1["stat"][field]:
                if key != "project":
                    source1["stat"][field][key] += source2["stat"][field][key]
