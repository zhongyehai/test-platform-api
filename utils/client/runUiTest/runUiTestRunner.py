# -*- coding: utf-8 -*-
import copy
import platform
import json
import os
import types
import importlib
from datetime import datetime
from threading import Thread

from flask.json import JSONEncoder

from app.config.models.config import Config
from utils.log import logger
from utils.parse.parse import encode_object, list_to_dict
from utils.util.fileUtil import BROWSER_DRIVER_ADDRESS, FileUtil
from utils.client.runUiTest.parseModel import ProjectFormatModel, ElementFormatModel, CaseFormatModel, StepFormatModel
from utils.client.runUiTest.uitestrunner.api import UiTestRunner
from utils.client.runUiTest.uitestrunner.utils import build_url
from app.assist.models.func import Func
from app.web_ui_test.models.project import WebUiProject as Project, WebUiProjectEnv as ProjectEnv
from app.web_ui_test.models.element import WebUiElement as Element
from app.web_ui_test.models.caseSet import WebUiCaseSet as CaseSet
from app.web_ui_test.models.case import WebUiCase as Case
from app.web_ui_test.models.step import WebUiStep as Step
from app.web_ui_test.models.report import WebUiReport as Report
from utils.message.sendReport import async_send_report, call_back_for_pipeline
from config.config import ui_action_mapping_reverse


class RunCase:
    """ 运行测试用例 """

    def __init__(self,
                 project_id=None,
                 run_name=None,
                 case_id=[],
                 task={},
                 report_id=None,
                 performer=None,
                 create_user=None,
                 is_async=True,
                 env=None):

        self.project_id = project_id
        self.run_name = run_name
        self.task = task
        self.environment = env
        self.parsed_project_dict = {}
        self.parsed_page_dict = {}
        self.parsed_element_dict = {}
        self.parsed_case_dict = {}

        self.case_id_list = case_id  # 要执行的用例id_list
        self.all_case_steps = []  # 所有测试步骤
        self.wait_time_out = Config.get_wait_time_out()

        if not report_id:
            self.report = Report.get_new_report(
                name=self.run_name,
                run_type='task',
                performer=performer,
                create_user=create_user,
                project_id=project_id,
                # trigger_type=self.trigger_type
            )

        self.report_id = report_id or self.report.id

        Func.create_func_file(self.environment)  # 创建所有函数文件

        # UiTestRunner需要的数据格式
        self.DataTemplate = {
            'is_async': is_async,
            'project': self.run_name,
            'project_mapping': {
                'functions': {},
                'variables': {}
            },
            'testcases': []
        }

        self.parse_all_case()

    def get_formated_project(self, project_id):
        """ 从已解析的服务字典中取指定id的服务，如果没有，则取出来解析后放进去 """
        if project_id not in self.parsed_project_dict:
            project = Project.get_first(id=project_id).to_dict()
            self.parse_functions(project['func_files'])

            env = ProjectEnv.get_first(env=self.environment, project_id=project['id']).to_dict()
            env.update(project)
            self.parsed_project_dict.update({project_id: ProjectFormatModel(**env)})
        return self.parsed_project_dict[project_id]

    def get_formated_element(self, element_id):
        """ 从已解析的元素字典中取指定id的元素，如果没有，则取出来解析后放进去 """
        if element_id not in self.parsed_element_dict:
            element = Element.get_first(id=element_id).to_dict()
            self.parsed_element_dict.update({element_id: ElementFormatModel(**element)})
        return self.parsed_element_dict[element_id]

    def get_formated_case(self, case_id):
        """ 从已解析的用例字典中取指定id的用例，如果没有，则取出来解析后放进去 """
        if case_id not in self.parsed_case_dict:
            case = Case.get_first(id=case_id)
            self.parse_functions(json.loads(case.func_files))
            self.parsed_case_dict.update({case_id: CaseFormatModel(**case.to_dict())})
        return self.parsed_case_dict[case_id]

    def parse_functions(self, func_list):
        """ 获取自定义函数 """
        for func_file_id in func_list:
            func_file_name = Func.get_first(id=func_file_id).name
            func_file_data = importlib.reload(importlib.import_module(f'func_list.{self.environment}_{func_file_name}'))
            self.DataTemplate['project_mapping']['functions'].update({
                name: item for name, item in vars(func_file_data).items() if isinstance(item, types.FunctionType)
            })

    def build_report(self, json_result):
        """ 写入测试报告到数据库, 并把数据写入到文本中 """
        result = json.loads(json_result)
        report = Report.get_first(id=self.report_id)
        report.update({'is_passed': 1 if result['success'] else 0, 'is_done': 1})

        # 测试报告写入到文本文件
        FileUtil.save_web_ui_test_report(report.id, json_result)

    def run_case(self):
        """ 调 HttpRunner().run() 执行测试 """

        logger.info(f'请求数据：\n{self.DataTemplate}')

        if self.DataTemplate.get('is_async', 0):  # 串行执行
            # 遍历case，以case为维度多线程执行，测试报告按顺序排列
            run_case_dict = {}
            for index, case in enumerate(self.DataTemplate['testcases']):
                run_case_dict[index] = False  # 用例运行标识，索引：是否运行完成
                temp_case = self.DataTemplate
                temp_case['testcases'] = [case]
                self._async_run_case(temp_case, run_case_dict, index)
        else:  # 并行执行
            self.sync_run_case()

    def _run_case(self, case, run_case_dict, index):
        runner = UiTestRunner()
        runner.run(case)
        self.update_run_case_status(run_case_dict, index, runner.summary)

    def _async_run_case(self, case, run_case_dict, index):
        """ 多线程运行用例 """
        Thread(target=self._run_case, args=[case, run_case_dict, index]).start()

    def send_report(self, res):
        """ 发送测试报告 """
        if self.task:
            content = json.loads(res)

            # 发送回调给流水线
            call_back_for_pipeline(self.task["call_back"] or [], content["success"])

            # 发送测试报告
            async_send_report(
                content=json.loads(res),
                **self.task,
                report_id=self.report_id,
                report_addr=Config.get_ui_report_addr()
            )

    def sync_run_case(self):
        """ 单线程运行用例 """
        runner = UiTestRunner()
        runner.run(self.DataTemplate)
        summary = runner.summary
        summary['time']['start_at'] = datetime.fromtimestamp(summary['time']['start_at']).strftime("%Y-%m-%d %H:%M:%S")
        summary['run_type'] = self.DataTemplate.get('is_async', 0)
        summary['run_env'] = self.environment
        jump_res = json.dumps(summary, ensure_ascii=False, default=encode_object, cls=JSONEncoder)
        self.build_report(jump_res)
        self.send_report(jump_res)

    def update_run_case_status(self, run_dict, run_index, summary):
        """ 每条用例执行完了都更新对应的运行状态，如果更新后的结果是用例全都运行了，则生成测试报告"""
        run_dict[run_index] = summary
        if all(run_dict.values()):  # 全都执行完毕
            all_summary = run_dict[0]
            all_summary['run_type'] = self.DataTemplate.get('is_async', 0)
            all_summary['run_env'] = self.environment
            all_summary['time']['start_at'] = datetime.fromtimestamp(all_summary['time']['start_at']).strftime(
                "%Y-%m-%d %H:%M:%S")
            for index, res in enumerate(run_dict.values()):
                if index != 0:
                    self.build_summary(all_summary, res, ['testcases', 'teststeps'])  # 合并用例统计, 步骤统计
                    all_summary['details'].extend(res['details'])  # 合并测试用例数据
                    all_summary['success'] = all([all_summary['success'], res['success']])  # 测试报告状态
                    all_summary['time']['duration'] = summary['time']['duration']  # 总共耗时取运行最长的

            jump_res = json.dumps(all_summary, ensure_ascii=False, default=encode_object, cls=JSONEncoder)
            self.build_report(jump_res)
            self.send_report(jump_res)

    def build_summary(self, source1, source2, fields):
        """ 合并测试报告统计 """
        for field in fields:
            for key in source1['stat'][field]:
                if key != 'project':
                    source1['stat'][field][key] += source2['stat'][field][key]

    def parse_step(self, project, element, step):
        """ 解析测试步骤
        project: 当前步骤对应元素所在的项目(解析后的)
        element: 解析后的element
        step: 原始step
        返回解析后的步骤 {}
        """
        return {
            'name': step.name,
            'setup_hooks': [up.strip() for up in step.up_func.split(';') if up] if step.up_func else [],
            'teardown_hooks': [func.strip() for func in step.down_func.split(';') if func] if step.down_func else [],
            'skip': '',  # 无条件跳过当前测试
            'skipIf': step.is_run is False,  # 如果条件为真，则跳过当前测试
            'skipUnless': '',  # 除非条件为真，否则跳过当前测试
            'times': step.run_times,  # 运行次数
            'extract': step.extracts,  # 要提取的信息
            'validate': step.validates,  # 断言信息
            "test_action": {
                'execute_name': step.execute_name,
                "action": step.execute_type,
                "by_type": element.by,
                # 如果是打开页面，则设置为项目域名+页面地址
                "element": build_url(project.host, element.element) if element.by == 'url' else element.element,
                "text": step.send_keys,
                "wait_time_out": float(step.wait_time_out or element.wait_time_out or self.wait_time_out)
            }
        }

    def parse_extracts(self, extracts: list):
        """ 解析数据提取
        extracts_list:
            [
                {'data_source': 'extract_09_value', 'key': 'name1', 'remark': None, 'value': 1},
                {'data_source': 'func', 'key': 'name2', 'remark': None, 'value': '$do_something()'},
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
            if extract['extract_type'] == 'func':  # 自定义函数提取
                parsed_list.append({
                    "type": "func",
                    "key": extract.get('key'),
                    "value": extract.get('value')
                })
            elif extract['extract_type']:  # 页面元素提取
                element = self.get_formated_element(extract["value"])
                parsed_list.append({
                    "type": "element",
                    "key": extract.get('key'),
                    "value": {
                        "action": extract.get('extract_type'),
                        "by_type": element.by,
                        "element": element.element
                    }
                })
        return parsed_list

    def parse_validates(self, validates_list):
        """ 解析断言
        validates:
            [{'element': 3, 'data_type': 'str', 'key': 'null', 'validate_type': 'assert_52_element_value_larger_than', 'value': '123123'}]
        return:
            [{
                "comparator": "validate_type",  # 断言方式
                "check": ("id", "kw"),  # 实际结果
                "expect": "123123"  # 预期结果
            }]
        """
        parsed_validate = []
        for validate in validates_list:
            if validate["validate_type"]:
                element = self.get_formated_element(validate["element"])
                parsed_validate.append({
                    "comparator": validate["validate_type"],  # 断言方式
                    "check": (element.by, element.element),  # 实际结果
                    "expect": self.build_expect_result(validate["data_type"], validate["value"])  # 预期结果
                })
        return parsed_validate

    def build_expect_result(self, data_type, value):
        """ 生成预期结果 """
        if data_type in ["variable", "func", 'str']:
            return value
        elif data_type == 'json':
            return json.dumps(json.loads(value))
        else:  # python数据类型
            return eval(f'{data_type}({value})')

    def get_all_steps(self, case_id: int, case_container):
        """ 解析引用的用例 """
        case = self.get_formated_case(case_id)

        # 保留用例设置的浏览器信息
        case_container['cookies'].append(case.cookies)
        case_container['session_storage'].append(case.session_storage)
        case_container['local_storage'].append(case.local_storage)

        steps = Step.query.filter_by(case_id=case.id, is_run=True).order_by(Step.num.asc()).all()
        for step in steps:
            if step.quote_case:
                self.get_all_steps(step.quote_case, case_container)
            else:
                self.all_case_steps.append(step)

    def parse_all_case(self):
        """ 解析所有用例 """

        # 遍历要运行的用例
        for case_id in self.case_id_list:

            case_container = {'cookies': [], 'session_storage': [], 'local_storage': []}  # 用例数据的容器
            project_container = {'cookies': [], 'session_storage': [], 'local_storage': []}  # 项目数据的容器

            current_case = Case.get_first(id=case_id)
            current_project = self.get_formated_project(CaseSet.get_first(id=current_case.set_id).project_id)

            # 用例格式模板, # 火狐：geckodriver
            browser_path = os.path.join(
                BROWSER_DRIVER_ADDRESS, f"chromedriver{'.exe' if 'Windows' in platform.platform() else ''}"
            )
            case_template = {
                'config': {
                    'variables': {},
                    'cookies': {},
                    'session_storage': {},
                    'local_storage': {},
                    'name': current_case.name,
                    "browser_type": "chrome",
                    "browser_path": browser_path
                },
                'teststeps': []
            }

            # 递归获取测试步骤（中间有可能某些测试步骤是引用的用例）
            self.get_all_steps(case_id, case_container)
            print(f'最后解析出的步骤为：{self.all_case_steps}')

            # 循环解析测试步骤
            all_variables = {}  # 当前用例的所有公共变量
            for step in self.all_case_steps:
                case = self.get_formated_case(step.case_id)
                element = self.get_formated_element(step.element_id)
                step = StepFormatModel(**step.to_dict())
                step.execute_name = ui_action_mapping_reverse[step.execute_type]  # 执行方式的别名，用于展示测试报告
                step.extracts = self.parse_extracts(step.extracts)  # 解析数据提取
                step.validates = self.parse_validates(step.validates)  # 解析断言
                project = self.get_formated_project(element.project_id)  # 元素所在的项目

                # 保留项目设置的浏览器信息
                project_container['cookies'].append(project.cookies)
                project_container['session_storage'].append(project.session_storage)
                project_container['local_storage'].append(project.local_storage)

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
                        step.name += driver_data.get('comment', '')
                        step.params = step.params = step.data_json = step.data_form = driver_data.get('data', {})
                        case_template['teststeps'].append(self.parse_step(project, element, step))
                else:
                    case_template['teststeps'].append(self.parse_step(project, element, step))

                # 把服务和用例的的自定义变量留下来
                all_variables.update(project.variables)
                all_variables.update(case.variables)

            # 更新当前服务+当前用例的自定义变量，最后以当前用例设置的自定义变量为准
            all_variables.update(current_project.variables)
            all_variables.update(self.get_formated_case(current_case.id).variables)
            case_template['config']['variables'].update(all_variables)

            # 合并预设的浏览器信息，当项目设置与用例设置的重复时，以用例设置的为准
            project_container['cookies'].extend(case_container['cookies'])
            project_container['session_storage'].extend(case_container['session_storage'])
            project_container['local_storage'].extend(case_container['local_storage'])

            # 更新预设的浏览器信息
            case_template['config']['cookies'] = list_to_dict(project_container['cookies'])
            case_template['config']['session_storage'] = list_to_dict(project_container['session_storage'])
            case_template['config']['local_storage'] = list_to_dict(project_container['local_storage'])

            # 设置的用例执行多少次就加入多少次
            name = case_template['config']['name']
            for index in range(current_case.run_times or 1):
                case_template['config']['name'] = f"{name}_{index + 1}" if current_case.run_times > 1 else name
                self.DataTemplate['testcases'].append(copy.deepcopy(case_template))

            # 完整的解析完一条用例后，去除对应的解析信息
            self.all_case_steps = []

        # 去除服务级的公共变量，保证用步骤上解析后的公共变量
        self.DataTemplate['project_mapping']['variables'] = {}
