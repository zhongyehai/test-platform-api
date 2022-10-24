# # encoding: utf-8
import time
import unittest

from . import (exceptions, logger, parser, report, runner)


class TestRunner(object):

    def __init__(self, failfast=False, log_level="INFO", log_file=None):
        """ 初始化 TestRunner.
        Args:
            failfast (bool): 设置为 True 时，测试在首次遇到错误或失败时会停止运行；默认值为 False
            log_level (str): 设置日志级别，默认为 "INFO"
            log_file (str): 设置日志文件路径，指定后将同时输出日志文件；默认不输出日志文件
        """
        self.exception_stage = "初始化TestRunner"
        kwargs = {
            "failfast": failfast,
            "resultclass": report.HtmlTestResult
        }
        self.unittest_runner = unittest.TextTestRunner(**kwargs)
        self.test_loader = unittest.TestLoader()
        self._summary = None
        if log_file:
            logger.setup_logger(log_level, log_file)

    def _add_case_to_suite(self, tests_mapping):
        """ 把测试步骤组装为测试套件
        Args:
            tests_mapping (dict): project info and testcases list.
        Returns:
            unittest.TestSuite()
        """
        def _build_step_function(test_runner, step_dict):
            """ 把测试数据构建为测试方法"""
            def test(self):
                try:
                    test_runner.run_test(step_dict)
                except exceptions.MyBaseFailure as ex:
                    self.fail(str(ex))
                finally:
                    self.meta_datas = test_runner.meta_datas

            test.__doc__ = step_dict["config"].get("name") if "config" in step_dict else step_dict.get("name")

            return test

        test_suite = unittest.TestSuite()
        functions = tests_mapping.get("project_mapping", {}).get("functions", {})

        for testcase in tests_mapping["testcases"]:
            config = testcase.get("config", {})
            test_runner = runner.Runner(config, functions)
            TestSequense = type('TestSequense', (unittest.TestCase,), {})

            steps = testcase.get("teststeps", [])
            for index, step_dict in enumerate(steps):
                for times_index in range(int(step_dict.get("times", 1))):
                    # 一条用例不超过9999个步骤，每个步骤运行次数不超过999次
                    test_function_name = 'test_{:04}_{:03}'.format(index, times_index)
                    test_function = _build_step_function(test_runner, step_dict)
                    setattr(TestSequense, test_function_name, test_function)

            loaded_testcase = self.test_loader.loadTestsFromTestCase(TestSequense)
            setattr(loaded_testcase, "config", config)
            setattr(loaded_testcase, "teststeps", steps)
            setattr(loaded_testcase, "runner", test_runner)
            test_suite.addTest(loaded_testcase)

        return test_suite

    def _run_suite(self, test_suite):
        """ 运行test_suite中的测试
        Args:
            test_suite: unittest.TestSuite()
        Returns:
            list: tests_results
        """
        tests_results = []

        for testcase in test_suite:
            logger.log_info(f'开始运行测试用例: {testcase.config.get("name")}')

            result = self.unittest_runner.run(testcase)
            tests_results.append((testcase, result))

        return tests_results

    def merge_test_result(self, tests_results, project_name):
        """ 汇总测试数据和结果
        Args:
            tests_results (list): list of (testcase, result)
        """
        summary = {
            "success": True,
            "stat": {
                "testcases": {
                    "project": project_name,
                    "total": len(tests_results),
                    "success": 0,
                    "fail": 0
                },
                "teststeps": {}
            },
            "time": {
                'start_at': time.time()
            },
            "platform": report.get_system_platform(),
            "details": []
        }

        for tests_result in tests_results:
            testcase, result = tests_result
            testcase_summary = report.build_summary(result)

            if testcase_summary["success"]:
                summary["stat"]["testcases"]["success"] += 1
            else:
                summary["stat"]["testcases"]["fail"] += 1

            summary["success"] &= testcase_summary["success"]
            testcase_summary["name"] = testcase.config.get("name")

            report.merge_stat(summary["stat"]["teststeps"], testcase_summary["stat"])
            report.merge_stat(summary["time"], testcase_summary["time"])

            summary["details"].append(testcase_summary)

        return summary

    def run(self, tests_dict):
        """ 运行testcase / testsuite数据 """

        self.exception_stage = "解析测试计划"
        parsed_tests_mapping = parser.parse_test_data(tests_dict)

        self.exception_stage = "添加测试到测试套件"
        test_suite = self._add_case_to_suite(parsed_tests_mapping)

        self.exception_stage = "运行测试套件"
        results = self._run_suite(test_suite)

        self.exception_stage = "生成测试结果"
        self._summary = self.merge_test_result(results, project_name=tests_dict.get('project'))

        self.exception_stage = "格式化测试报告数据"
        report.format_summary(self._summary)

    @property
    def summary(self):
        """ 获取测试结果和数据 """
        return self._summary
