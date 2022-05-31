# -*- coding: utf-8 -*-

import platform
import json
import os
import types
import importlib
from datetime import datetime

from flask.json import JSONEncoder

from app.utils.log import logger
from app.utils.parse import encode_object
from app.utils.globalVariable import UI_REPORT_ADDRESS, BROWSER_DRIVER_ADDRESS, run_ui_test_log
from app.utils.runUiTest.parseModel import ProjectFormatModel, ElementFormatModel, CaseFormatModel, StepFormatModel
from app.utils.runUiTest.uitestrunner.api import UiTestRunner
from app.baseModel import db
from app.api_test.func.models import Func
from app.ui_test.project.models import UiProject as Project, UiProjectEnv as ProjectEnv
from app.ui_test.element.models import UiElement as Element
from app.ui_test.caseSet.models import UiCaeSet as Set
from app.ui_test.case.models import UiCase as Case
from app.ui_test.step.models import UiStep as Step
from app.ui_test.report.models import UiReport as Report
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
                 create_user=None):

        self.project_id = project_id
        self.run_name = run_name

        # 环境，如果是定时任务就取定时任务设置的环境，否则取用例选择的环境
        self.task = task
        if self.task:
            self.environment = task.get('choice_host') if isinstance(task, dict) else task.choice_host
        else:
            self.environment = Case.get_first(id=case_id[0]).choice_host

        self.parsed_project_dict = {}
        self.parsed_page_dict = {}
        self.parsed_element_dict = {}
        self.parsed_case_dict = {}

        self.case_id_list = case_id  # 要执行的用例id_list
        self.all_case_steps = []  # 所有测试步骤

        if not report_id:
            self.report = Report.get_new_report(self.run_name, 'task', performer, create_user, project_id)

        self.report_id = report_id or self.report.id

        Func.create_func_file()  # 创建所有函数文件
        self.func_file_list = Func.get_all()

        # UiTestRunner需要的数据格式
        self.DataTemplate = {
            'project': self.run_name,  # or self.get_formated_project(self.project_id).name,
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
            env = ProjectEnv.get_first(env=self.environment, project_id=project['id']).to_dict()
            self.parse_functions(env['func_files'])
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
            func_file_data = importlib.reload(importlib.import_module('func_list.{}'.format(func_file_name)))
            self.DataTemplate['project_mapping']['functions'].update({
                name: item for name, item in vars(func_file_data).items() if isinstance(item, types.FunctionType)
            })

    def parse_api(self, project, api):
        """ 把解析后的接口对象 解析为httpRunner的数据结构 """
        return {
            'name': api.name,  # 接口名
            'setup_hooks': [up.strip() for up in api.up_func.split(';') if up] if api.up_func else [],
            'teardown_hooks': [func.strip() for func in api.down_func.split(';') if func] if api.down_func else [],
            'skip': '',  # 无条件跳过当前测试
            'skipIf': '',  # 如果条件为真，则跳过当前测试
            'skipUnless': '',  # 除非条件为真，否则跳过当前测试
            'times': 1,  # 运行次数
            'extract': api.extracts,  # 接口要提取的信息
            'validate': api.validates,  # 接口断言信息
            'base_url': project.host,
            'data_type': api.data_type,
            'request': {
                'method': api.method,
                'url': api.addr,
                'headers': api.headers,  # 接口头部信息
                'params': api.params,  # 接口查询字符串参数
                'json': api.data_json,
                'data': api.data_form['string'] if api.data_type.upper() == 'DATA' else api.data_xml,
                'files': api.data_form['files'] if api.data_form else {},
            }
        }

    def build_report(self, json_result):
        """ 写入测试报告到数据库, 并把数据写入到文本中 """
        result = json.loads(json_result)
        report = Report.get_first(id=self.report_id)
        with db.auto_commit():
            report.is_passed = 1 if result['success'] else 0
            report.is_done = 1

        # 测试报告写入到文本文件
        with open(os.path.join(UI_REPORT_ADDRESS, f'{report.id}.txt'), 'w') as f:
            f.write(json_result)

    def run_case(self):
        """ 调 UiTestRunner().run() 执行测试 """
        logger.info(f'请求数据：\n{self.DataTemplate}')
        runner = UiTestRunner()
        runner.run(self.DataTemplate)
        summary = runner.summary
        summary['time']['start_at'] = datetime.fromtimestamp(summary['time']['start_at']).strftime("%Y-%m-%d %H:%M:%S")
        jump_res = json.dumps(summary, ensure_ascii=False, default=encode_object, cls=JSONEncoder)
        self.build_report(jump_res)
        return jump_res

    def parse_step(self, current_project, project, case, element, step):
        """ 解析测试步骤
        current_project: 当前用例所在的服务(解析后的)
        project: 当前步骤对应接口所在的服务(解析后的)
        case: 解析后的case
        element: 解析后的element
        step: 原始step
        返回解析后的步骤 {}
        """
        # 解析头部信息，继承
        headers = {}
        headers.update(current_project.headers)
        headers.update(project.headers)
        # headers.update(api['request']['headers'])
        headers.update(case.headers)

        # 如果是打开页面，则设置为项目域名+页面地址
        if element.by == 'url':
            element.element = project.host + element.element

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
                "element": element.element,
                "text": step.send_keys
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
            if extract['extract_type'] == 'func':    # 自定义函数提取
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

    def get_all_steps(self, case_id: int):
        """ 解析引用的用例 """
        case = self.get_formated_case(case_id)
        steps = Step.query.filter_by(case_id=case.id, is_run=True).order_by(Step.num.asc()).all()
        for step in steps:
            if step.quote_case:
                self.get_all_steps(step.quote_case)
            else:
                self.all_case_steps.append(step)

    def parse_all_case(self):
        """ 解析所有用例 """

        # 遍历要运行的用例
        for case_id in self.case_id_list:

            current_case = Case.get_first(id=case_id)
            current_project = self.get_formated_project(Set.get_first(id=current_case.set_id).project_id)

            # 选择运行环境
            if not self.task:
                self.environment = current_case.choice_host

            # 用例格式模板, # 火狐：geckodriver
            case_template = {
                'config': {
                    'variables': {},
                    'headers': {},
                    'name': current_case.name,
                    "browser_type": "chrome",
                    "browser_path": os.path.join(BROWSER_DRIVER_ADDRESS, f"chromedriver{'.exe' if 'Windows' in platform.platform() else ''}"),
                    "web_driver_time_out": 5,  # 浏览器等待元素超时时间
                },
                'teststeps': []
            }

            # 递归获取测试步骤（中间有可能某些测试步骤是引用的用例）
            self.get_all_steps(case_id)
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
                project = self.get_formated_project(element.project_id)

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
                        case_template['teststeps'].append(
                            self.parse_step(current_project, project, case, element, step))
                else:
                    case_template['teststeps'].append(self.parse_step(current_project, project, case, element, step))

                # 把服务和用例的的自定义变量留下来
                all_variables.update(project.variables)
                all_variables.update(case.variables)

            # 更新当前服务+当前用例的自定义变量，最后以当前用例设置的自定义变量为准
            # current_project_variables = current_project.variables
            # current_project_variables.update(all_variables)
            all_variables.update(current_project.variables)
            all_variables.update(self.get_formated_case(current_case.id).variables)
            case_template['config']['variables'].update(all_variables)  # = all_variables

            # 设置的用例执行多少次就加入多少次
            for i in range(current_case.run_times or 1):
                self.DataTemplate['testcases'].append(case_template)

            # 完整的解析完一条用例后，去除对应的解析信息
            self.all_case_steps = []

        # 去除服务级的公共变量，保证用步骤上解析后的公共变量
        self.DataTemplate['project_mapping']['variables'] = {}
