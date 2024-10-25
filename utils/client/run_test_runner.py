# -*- coding: utf-8 -*-
import copy
import json
import types
import importlib
from threading import Thread

from apps import create_app
from apps.api_test.model_factory import ApiCaseSuite, ApiMsg, ApiCase, ApiStep, ApiProject, ApiProjectEnv, ApiReport, \
    ApiReportCase, ApiReportStep
from apps.system.models.user import User
from apps.ui_test.model_factory import WebUiProject, WebUiProjectEnv, WebUiElement, WebUiCaseSuite, WebUiCase, \
    WebUiStep, \
    WebUiReport, WebUiReportCase, WebUiReportStep
from apps.app_test.model_factory import AppUiProject, AppUiProjectEnv, AppUiElement, AppUiCaseSuite, AppUiCase, \
    AppUiStep, AppUiReport, AppUiReportCase, AppUiReportStep
from apps.config.model_factory import RunEnv, WebHook
from apps.assist.model_factory import Script, Hits
from apps.config.model_factory import Config
from apps.enums import TriggerTypeEnum, ReceiveTypeEnum
from utils.client.test_runner.api import TestRunner
from utils.client.test_runner.utils import build_url
from utils.client.test_runner import built_in
from utils.client.parse_model import ProjectModel, ApiModel, CaseModel, ElementModel
from utils.logs.log import logger
from utils.message.send_report import async_send_report, call_back_for_pipeline


class RunTestRunner:

    def __init__(
            self, report_id=None, env_code=None, env_name=None, run_type="api", extend={}, task_dict={}):
        self.env_code = env_code  # 运行环境id
        self.env_name = env_name  # 运行环境名，用于发送即时通讯
        self.extend = extend
        self.report_id = report_id
        self.run_type = run_type
        self.task_dict = task_dict

        self.time_out = 60
        self.wait_time_out = 5
        self.count_step = 0
        self.api_set = set()
        self.element_set = set()
        self.parsed_project_dict = {}
        self.parsed_case_dict = {}
        self.parsed_api_dict = {}
        self.parsed_element_dict = {}
        self.run_env = None
        self.report = None

        self.api_model = ApiMsg
        self.element_model = None
        if self.run_type == "api":  # 接口自动化
            self.project_model = ApiProject
            self.project_env_model = ApiProjectEnv
            self.suite_model = ApiCaseSuite
            self.case_model = ApiCase
            self.step_model = ApiStep
            self.report_model = ApiReport
            self.report_case_model = ApiReportCase
            self.report_step_model = ApiReportStep
            self.time_out = Config.get_request_time_out()
            self.front_report_addr = f'{Config.get_report_host()}{Config.get_api_report_addr()}'
        elif self.run_type == "ui":  # web-ui自动化
            self.project_model = WebUiProject
            self.project_env_model = WebUiProjectEnv
            self.element_model = WebUiElement
            self.suite_model = WebUiCaseSuite
            self.case_model = WebUiCase
            self.step_model = WebUiStep
            self.report_model = WebUiReport
            self.report_case_model = WebUiReportCase
            self.report_step_model = WebUiReportStep
            self.wait_time_out = Config.get_wait_time_out()
            self.front_report_addr = f'{Config.get_report_host()}{Config.get_web_ui_report_addr()}'
        else:  # app-ui自动化
            self.project_model = AppUiProject
            self.project_env_model = AppUiProjectEnv
            self.element_model = AppUiElement
            self.suite_model = AppUiCaseSuite
            self.case_model = AppUiCase
            self.step_model = AppUiStep
            self.report_model = AppUiReport
            self.report_case_model = AppUiReportCase
            self.report_step_model = AppUiReportStep
            self.wait_time_out = Config.get_wait_time_out()
            self.front_report_addr = f'{Config.get_report_host()}{Config.get_app_ui_report_addr()}'

        # testRunner需要的数据格式
        self.run_test_data = {
            "is_async": 0,
            "run_type": self.run_type,
            "report_id": self.report_id,
            "report_model": self.report_model,
            "report_case_model": self.report_case_model,
            "report_step_model": self.report_step_model,
            "project_mapping": {
                "functions": {},
                "variables": {},
            },
            "report_case_list": [],  # 用例
        }

        self.init_parsed_data()

    def init_parsed_data(self):
        self.parsed_project_dict = {}
        self.parsed_case_dict = {}
        self.parsed_api_dict = {}
        self.parsed_element_dict = {}
        self.run_env = None

    def get_report_addr(self):
        """ 获取报告前端地址 """
        report_host = Config.get_report_host()
        if self.run_type == "api":  # 接口自动化
            report_addr = Config.get_api_report_addr()
            return f'{report_host}{report_addr}'
        elif self.run_type == "ui":  # web-ui自动化
            report_addr = Config.get_web_ui_report_addr()
            return f'{report_host}{report_addr}'
        else:  # app-ui自动化
            report_addr = Config.get_app_ui_report_addr()
            return f'{report_host}{report_addr}'

    def get_format_project(self, project_id):
        """ 从已解析的服务字典中取指定id的服务，如果没有，则取出来解析后放进去 """
        if not self.run_env:
            self.run_env = RunEnv.get_first(code=self.env_code).to_dict()

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
            self.parse_functions(case.script_list)
            self.parsed_case_dict.update({case_id: CaseModel(**case.to_dict())})
        return self.parsed_case_dict[case_id]

    def get_format_element(self, element_id):
        """ 从已解析的元素字典中取指定id的元素，如果没有，则取出来解析后放进去 """
        if element_id not in self.parsed_element_dict:
            element = self.element_model.get_first(id=element_id).to_dict()
            self.parsed_element_dict.update({element_id: ElementModel(**element)})
        return self.parsed_element_dict[element_id]

    def get_format_api(self, project, api_id=None, api_obj=None):
        """ 从已解析的接口字典中取指定id的接口，如果没有，则取出来解析后放进去 """
        if api_obj:
            api_id = api_obj.id
        if api_id not in self.parsed_api_dict:
            api = api_obj or ApiMsg.get_first(id=api_id)
            if api.project_id not in self.parsed_project_dict:
                self.parse_functions(json.loads(self.project_model.get_first(id=api.project_id).script_list))
            self.parsed_api_dict.update({
                api.id: self.parse_api(project, ApiModel(**api.to_dict()))
            })
        return self.parsed_api_dict[api_id]

    def parse_functions(self, func_list):
        """ 获取自定义函数 """
        for func_file_id in func_list:
            func_file_name = Script.get_first(id=func_file_id).name
            func_file_data = importlib.reload(importlib.import_module(f'script_list.{self.env_code}_{func_file_name}'))
            self.run_test_data["project_mapping"]["functions"].update({
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
                comparator = getattr(built_in, skip_if["comparator"])  # 借用断言来判断条件是否为真
                skip_if_result = comparator(skip_if["check_value"], skip_if["expect"])  # 通过没有返回值
            except Exception as error:
                skip_if_result = error
            if (skip_type == "and" and skip_if_result is None) or (skip_type == "or" and skip_if_result is None):
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
            "setup_hooks": step.up_func,
            "teardown_hooks": step.down_func,
            # "skip": not step.status,  # 无条件跳过当前测试
            "skip_if": step.skip_if,  # 如果条件为真，则跳过当前测试
            # "skip_unless": "",  # 除非条件为真，否则跳过当前测试
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

    def save_report_and_send_message(self, result):
        """ 写入测试报告到数据库, 并把数据写入到文本中 """
        logger.info(f'开始保存测试报告')
        self.report.save_report_start()
        self.report.update_report_result(result["result"], summary=result)
        self.report.save_report_finish()
        self.push_hit_if_fail(result["result"])
        logger.info(f'测试报告保存完成')

        # 有可能是多环境一次性批量运行，根据batch_id查是否全部运行完毕
        if self.report_model.select_is_all_done_by_batch_id(self.report.batch_id):  # 查询此batch_id下的报告是否全部生成
            if self.task_dict.get("merge_notify") != 1:  # 不合并通知
                # 有失败的，则获取失败的报告
                not_passed = self.report_model.db.session.query(
                    self.report_model.id, self.report_model.summary
                ).filter_by(batch_id=self.report.batch_id, is_passed=0).first()
                if not_passed:
                    self.send_report_if_task([{"report_id": not_passed[0], "report_summary": not_passed[1]}])
                else:
                    self.send_report_if_task([{"report_id": self.report.id, "report_summary": result}])
            else:  # 合并通知
                # 获取当前批次下的所有测试报告，summary
                query_res = self.report_model.db.session.query(
                    self.report_model.id, self.report_model.summary).filter_by(batch_id=self.report.batch_id).all()
                self.send_report_if_task([{"report_id": query[0], "report_summary": query[1]} for query in query_res])

    def run_case(self):
        """ 调 testRunner().run() 执行测试 """
        logger.info(f'\n测试执行数据：\n{self.run_test_data}')

        if self.run_test_data.get("is_async", 0):
            # 并行执行, 遍历case，以case为维度多线程执行，测试报告按顺序排列
            run_case_res_dict = {}
            self.report.run_case_start()
            for index, case in enumerate(self.run_test_data["report_case_list"]):
                run_case_res_dict[index] = False  # 用例运行标识，索引：是否运行完成
                run_case_template = copy.deepcopy(self.run_test_data)
                run_case_template["report_case_list"] = [case]
                Thread(target=self.run_case_on_new_thread, args=[run_case_template, run_case_res_dict, index]).start()
        else:  # 串行执行
            self.sync_run_case()

    def run_case_on_new_thread(self, run_case_template, run_case_res_dict, index):
        """ 新线程运行用例 """
        with create_app().app_context():  # 手动入栈
            runner = TestRunner()
            runner.run(run_case_template)
            self.update_run_case_status(run_case_res_dict, index, runner.summary)

    def update_run_case_status(self, run_case_res_dict, run_index, summary):
        """ 每条用例执行完了都更新对应的运行状态，如果更新后的结果是用例全都运行了，则生成测试报告"""
        run_case_res_dict[run_index] = summary
        if all(run_case_res_dict.values()):  # 全都执行完毕
            self.report.run_case_finish()
            all_summary = run_case_res_dict[0]
            all_summary["stat"]["count"]["step"] = self.count_step
            all_summary["stat"]["count"]["api"] = len(self.api_set)
            all_summary["stat"]["count"]["element"] = len(self.element_set)
            for index, res in enumerate(run_case_res_dict.values()):
                if index != 0:
                    self.build_summary(all_summary, res, ["test_case", "test_step"])  # 合并用例统计, 步骤统计
                    all_summary["result"] = 'success' if all_summary["result"] == 'success' and res[
                        "result"] == 'success' else 'fail'  # 测试报告状态
                    all_summary["time"]["case_duration"] = summary["time"]["case_duration"]  # 总共耗时取运行最长的
                    all_summary["time"]["step_duration"] = summary["time"]["step_duration"]  # 总共耗时取运行最长的
            self.save_report_and_send_message(all_summary)

    def sync_run_case(self):
        """ 串行运行用例 """
        self.report.run_case_start()
        runner = TestRunner()
        runner.run(self.run_test_data)
        self.report.run_case_finish()
        logger.info(f'测试执行完成，开始保存测试报告和发送报告')
        summary = runner.summary
        summary["stat"]["count"]["step"] = self.count_step
        summary["stat"]["count"]["api"] = len(self.api_set)
        summary["stat"]["count"]["element"] = len(self.element_set)
        self.save_report_and_send_message(summary)

    def send_report_if_task(self, notify_list):
        """ 发送测试报告 """
        if self.task_dict:
            self.call_back_to_pipeline(notify_list)  # 回调流水线

            # 发送测试报告
            logger.info(f'开始发送测试报告')

            if self.task_dict["receive_type"] == ReceiveTypeEnum.email: # 邮件
                email_server = Config.db.session.query(Config.value).filter(Config.name == self.task_dict["email_server"]).first()
                self.task_dict["email_server"] = email_server[0]
                email_from = User.db.session.query(User.email, User.email_password).filter(User.id == self.task_dict["email_from"]).first()
                self.task_dict["email_from"], self.task_dict["email_pwd"] = email_from[0], email_from[1]
                email_to = User.db.session.query(User.email).filter(User.id.in_(self.task_dict["email_to"])).all()
                self.task_dict["email_to"] = [email[0] for email in email_to]
            else: # 解析并组装webhook地址并加签
                self.task_dict["webhook_list"] = WebHook.get_webhook_list(
                    self.task_dict["receive_type"], self.task_dict["webhook_list"])

            async_send_report(content_list=notify_list, **self.task_dict, report_addr=self.front_report_addr)

    def call_back_to_pipeline(self, notify_list):
        """ 如果是流水线触发的，则回调给流水线 """
        if self.report.trigger_type == TriggerTypeEnum.pipeline:
            all_res = [notify["report_summary"]["result"] for notify in notify_list]
            call_back_for_pipeline(
                self.task_dict["id"],
                self.task_dict["call_back"] or [],
                self.extend,
                "fail" if "fail" in all_res else "success"
            )

    def push_hit_if_fail(self, result):
        """ 如果测试为不通过，且设置了要自动保存问题记录，且处罚类型为定时任务或者流水线触发，则保存 """
        if self.task_dict:
            # logger.info(f'开始保存问题记录')
            if (result == "fail" and self.task_dict["push_hit"] == 1
                    and self.report.trigger_type in [TriggerTypeEnum.cron, TriggerTypeEnum.pipeline]):
                Hits.model_create({
                  "hit_type": "巡检不通过",
                  "hit_detail": "",
                  "test_type": self.run_type,
                  "project_id": self.report.project_id,
                  "env": self.env_code,
                  "record_from": 2,  # 自动记录
                  "report_id": self.report.id,
                  "desc": "自动化测试创建"
                })

    @staticmethod
    def parse_api(project, api):
        """ 把解析后的接口对象 解析为testRunner的数据结构 """
        return {
            "id": api.id,
            "name": api.name,  # 接口名
            "setup_hooks": api.up_func,
            "teardown_hooks": api.down_func,
            "skip": "",  # 无条件跳过当前测试
            "skip_if": "",  # 如果条件为真，则跳过当前测试
            "skip_unless": "",  # 除非条件为真，否则跳过当前测试
            "times": 1,  # 运行次数
            "extract": api.extracts,  # 接口要提取的信息
            "validate": api.validates,  # 接口断言信息
            "base_url": project.host,
            "body_type": api.body_type,
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
    def build_summary(source1, source2, field_list):
        """ 合并测试报告统计 """
        for field in field_list:
            for key in source1["stat"][field]:
                source1["stat"][field][key] += source2["stat"][field][key]
