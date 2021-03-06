# -*- coding: utf-8 -*-

import json
import os
import types
import importlib
from threading import Thread
from datetime import datetime

from flask.json import JSONEncoder

from app.api_test.models.caseSet import ApiSet as Set
from app.api_test.models.api import ApiMsg
from app.api_test.models.case import ApiCase as Case
from app.api_test.models.step import ApiStep as Step
from app.assist.models.func import Func
from app.api_test.models.project import ApiProject as Project, ApiProjectEnv as ProjectEnv
from app.api_test.models.report import ApiReport as Report
from utils.client.runApiTest.httprunner.api import HttpRunner
from utils.log import logger
from utils.globalVariable import API_REPORT_ADDRESS
from utils.parse import encode_object
from utils.client.runApiTest.parseModel import ProjectFormatModel, ApiFormatModel, CaseFormatModel, StepFormatModel
from utils.sendReport import async_send_report


class BaseParse:

    def __init__(self, project_id=None, name=None, report_id=None, performer=None, create_user=None, env=None):

        self.environment = env  # 运行环境
        self.project_id = project_id
        self.run_name = name

        self.report_id = report_id or Report.get_new_report(self.run_name, 'task', performer, create_user, project_id).id
        self.parsed_project_dict = {}
        self.parsed_case_dict = {}
        self.parsed_api_dict = {}

        Func.create_func_file(self.environment)  # 创建所有函数文件

        # httpRunner需要的数据格式
        self.DataTemplate = {
            'is_async': False,
            'project': self.run_name,
            'project_mapping': {
                'functions': {},
                'variables': {}
            },
            'testcases': []
        }

    def get_formated_project(self, project_id):
        """ 从已解析的服务字典中取指定id的服务，如果没有，则取出来解析后放进去 """
        if project_id not in self.parsed_project_dict:
            project = Project.get_first(id=project_id).to_dict()
            env = ProjectEnv.get_first(env=self.environment, project_id=project['id']).to_dict()
            self.parse_functions(env['func_files'])
            env.update(project)

            self.parsed_project_dict.update({project_id: ProjectFormatModel(**env)})
        return self.parsed_project_dict[project_id]

    def get_formated_case(self, case_id):
        """ 从已解析的用例字典中取指定id的用例，如果没有，则取出来解析后放进去 """
        if case_id not in self.parsed_case_dict:
            case = Case.get_first(id=case_id)
            self.parse_functions(json.loads(case.func_files))
            self.parsed_case_dict.update({case_id: CaseFormatModel(**case.to_dict())})
        return self.parsed_case_dict[case_id]

    def get_formated_api(self, project, api):
        """ 从已解析的接口字典中取指定id的接口，如果没有，则取出来解析后放进去 """
        if api.id not in self.parsed_api_dict:
            if api.project_id not in self.parsed_project_dict:
                self.parse_functions(json.loads(Project.get_first(id=api.project_id).func_files))
            self.parsed_api_dict.update({
                api.id: self.parse_api(project, ApiFormatModel(**api.to_dict()))
            })
        return self.parsed_api_dict[api.id]

    def parse_functions(self, func_list):
        """ 获取自定义函数 """
        for func_file_id in func_list:
            func_file_name = Func.get_first(id=func_file_id).name
            func_file_data = importlib.reload(importlib.import_module(f'func_list.{self.environment}_{func_file_name}'))
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
        report.update({'is_passed': 1 if result['success'] else 0, 'is_done': 1})

        # 测试报告写入到文本文件
        with open(os.path.join(API_REPORT_ADDRESS, f'{report.id}.txt'), 'w') as f:
            f.write(json_result)

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
        runner = HttpRunner()
        runner.run(case)
        self.update_run_case_status(run_case_dict, index, runner.summary)

    def _async_run_case(self, case, run_case_dict, index):
        """ 多线程运行用例 """
        Thread(target=self._run_case, args=[case, run_case_dict, index]).start()

    def sync_run_case(self):
        """ 单线程运行用例 """
        runner = HttpRunner()
        runner.run(self.DataTemplate)
        summary = runner.summary
        summary['time']['start_at'] = datetime.fromtimestamp(summary['time']['start_at']).strftime("%Y-%m-%d %H:%M:%S")
        summary['run_type'] = self.DataTemplate.get('is_async', 0)
        summary['run_env'] = self.environment
        jump_res = json.dumps(summary, ensure_ascii=False, default=encode_object, cls=JSONEncoder)
        self.build_report(jump_res)
        self.send_report(jump_res)

        # if self.task:  # 多线程发送测试报告
        #     async_send_report(content=json.loads(jump_res), **self.task, report_id=self.report_id)

    def update_run_case_status(self, run_dict, run_index, summary):
        """ 每条用例执行完了都更新对应的运行状态，如果更新后的结果是用例全都运行了，则生成测试报告"""
        run_dict[run_index] = summary
        if all(run_dict.values()):  # 全都执行完毕
            all_summary = run_dict[0]
            all_summary['run_type'] = self.DataTemplate.get('is_async', 0)
            summary['run_env'] = self.environment
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

            # if self.task:  # 多线程发送测试报告
            #     async_send_report(content=json.loads(jump_res), **self.task, report_id=self.report_id)

    def send_report(self, res):
        """ 发送测试报告 """
        if self.task:
            async_send_report(content=json.loads(res), **self.task, report_id=self.report_id)

    def build_summary(self, source1, source2, fields):
        """ 合并测试报告统计 """
        for field in fields:
            for key in source1['stat'][field]:
                if key != 'project':
                    source1['stat'][field][key] += source2['stat'][field][key]


class RunApi(BaseParse):
    """ 接口调试 """

    def __init__(self, project_id=None, run_name=None, api_ids=None, report_id=None, task=None, env='test'):
        super().__init__(project_id=project_id, name=run_name, report_id=report_id, env=env)

        self.task = task
        # 要执行的接口id
        self.api_ids = api_ids

        # 解析当前服务信息
        self.project = self.get_formated_project(self.project_id)

        # 解析api
        self.format_data_for_template()

    def format_data_for_template(self):
        """ 接口调试 """
        logger.info(f'本次测试的接口id：\n{self.api_ids}')

        # 用例的数据结构
        test_case_template = {
            'config': {
                'variables': {},
            },
            'teststeps': []  # 测试步骤
        }

        # 解析api
        for api_obj in self.api_ids:
            api = self.get_formated_api(self.project, api_obj)

            # 合并头部信息
            headers = {}
            headers.update(self.project.headers)
            headers.update(api['request']['headers'])
            api['request']['headers'] = headers

            # 把api加入到步骤
            test_case_template['teststeps'].append(api)

        # 更新公共变量
        test_case_template['config']['variables'].update(self.project.variables)
        self.DataTemplate['testcases'].append(test_case_template)


class RunCase(BaseParse):
    """ 运行测试用例 """

    def __init__(self, project_id=None, run_name=None, case_id=[], task={}, report_id=None, performer=None,
                 create_user=None, is_async=True, env='test'):
        super().__init__(project_id=project_id, name=run_name, report_id=report_id, performer=performer,
                         create_user=create_user, env=env)

        self.task = task
        self.DataTemplate['is_async'] = is_async

        # 接口对应的服务字典，在需要解析服务时，先到这里面查，没有则去数据库取出来解析
        self.projects_dict = {}

        # 步骤对应的接口字典，在需要解析字典时，先到这里面查，没有则去数据库取出来解析
        self.apis_dict = {}

        # 要执行的用例id_list
        self.case_id_list = case_id

        # 所有测试步骤
        self.all_case_steps = []
        self.parse_all_case()

    def parse_step(self, current_project, project, case, api, step):
        """ 解析测试步骤
        current_project: 当前用例所在的服务(解析后的)
        project: 当前步骤对应接口所在的服务(解析后的)
        case: 解析后的case
        api: 解析后的api
        step: 原始step
        返回解析后的步骤 {}
        """
        # 解析头部信息，继承
        headers = {}
        headers.update(current_project.headers)
        headers.update(project.headers)
        # headers.update(api['request']['headers'])
        headers.update(case.headers)
        headers.update(step.headers)

        return {
            'name': step.name,
            'setup_hooks': [up.strip() for up in step.up_func.split(';') if up] if step.up_func else [],
            'teardown_hooks': [func.strip() for func in step.down_func.split(';') if func] if step.down_func else [],
            'skip': '',  # 无条件跳过当前测试
            'skipIf': step.is_run,  # 如果条件为真，则跳过当前测试
            'skipUnless': '',  # 除非条件为真，否则跳过当前测试
            'times': step.run_times,  # 运行次数
            'extract': step.extracts,  # 接口要提取的信息
            'validate': step.validates,  # 接口断言信息
            'base_url': current_project.host if step.replace_host else project.host,
            'request': {
                'method': api['request']['method'],
                'url': api['request']['url'],
                'headers': headers,  # 接口头部信息
                'params': step.params,  # 接口查询字符串参数
                'json': step.data_json,
                'data': step.data_form.get('string', {}) if api['data_type'] in ('DATA', 'FORM') else step.data_xml,
                'files': step.data_form.get('files', {}),
            }
        }

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

            # 用例格式模板
            case_template = {
                'config': {
                    'variables': {},
                    'headers': {},
                    'name': current_case.name
                },
                'teststeps': []
            }

            # 递归获取测试步骤（中间有可能某些测试步骤是引用的用例）
            self.get_all_steps(case_id)
            print(f'最后解析出的步骤为：{self.all_case_steps}')

            # 循环解析测试步骤
            all_variables = {}  # 当前用例的所有公共变量
            for step in self.all_case_steps:
                step = StepFormatModel(**step.to_dict())
                case = self.get_formated_case(step.case_id)
                api_temp = ApiMsg.get_first(id=step.api_id)
                project = self.get_formated_project(api_temp.project_id)
                api = self.get_formated_api(project, api_temp)

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
                        case_template['teststeps'].append(self.parse_step(current_project, project, case, api, step))
                else:
                    case_template['teststeps'].append(self.parse_step(current_project, project, case, api, step))

                # 把服务和用例的的自定义变量留下来
                all_variables.update(project.variables)
                all_variables.update(case.variables)

            # 更新当前服务+当前用例的自定义变量，最后以当前用例设置的自定义变量为准
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
