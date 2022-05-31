# encoding: utf-8
import time
import unittest
from . import (exceptions, loader, logger, parser, report, runner, utils, validator)


class HttpRunner(object):

    def __init__(self, failfast=False, save_tests=False, report_template=None, report_dir=None, log_level="INFO", log_file=None):
        """ 初始化 HttpRunner.
        Args:
            failfast (bool): 设置为 True 时，测试在首次遇到错误或失败时会停止运行；默认值为 False
            save_tests (bool): 设置为 True 时，会将运行过程中的状态（loaded/parsed/summary）保存为 JSON 文件，存储于 logs 目录下；默认为 False
            report_template (str): 测试报告模板文件路径，模板应为Jinja2格式。
            report_dir (str): html报告保存目录。
            log_level (str): 设置日志级别，默认为 "INFO"
            log_file (str): 设置日志文件路径，指定后将同时输出日志文件；默认不输出日志文件
        """
        self.exception_stage = "initialize HttpRunner()"
        kwargs = {
            "failfast": failfast,
            "resultclass": report.HtmlTestResult
        }
        self.unittest_runner = unittest.TextTestRunner(**kwargs)
        self.test_loader = unittest.TestLoader()
        self.save_tests = save_tests
        self.report_template = report_template
        self.report_dir = report_dir
        self._summary = None
        if log_file:
            logger.setup_logger(log_level, log_file)

    def _add_tests(self, tests_mapping):
        """ initialize testcase with Runner() and add to test suite.

        Args:
            tests_mapping (dict): project info and testcases list.

        Returns:
            unittest.TestSuite()

        """
        def _add_test(test_runner, test_dict):
            """ 将测试添加到测试用例。"""
            def test(self):
                try:
                    test_runner.run_test(test_dict)
                except exceptions.MyBaseFailure as ex:
                    self.fail(str(ex))
                finally:
                    self.meta_datas = test_runner.meta_datas

            if "config" in test_dict:
                # run nested testcase
                test.__doc__ = test_dict["config"].get("name")
            else:
                # run api test
                test.__doc__ = test_dict.get("name")

            return test

        test_suite = unittest.TestSuite()
        functions = tests_mapping.get("project_mapping", {}).get("functions", {})

        for testcase in tests_mapping["testcases"]:
            config = testcase.get("config", {})
            test_runner = runner.Runner(config, functions)
            TestSequense = type('TestSequense', (unittest.TestCase,), {})

            tests = testcase.get("teststeps", [])
            for index, test_dict in enumerate(tests):
                for times_index in range(int(test_dict.get("times", 1))):
                    # suppose one testcase should not have more than 9999 steps,
                    # and one step should not run more than 999 times.
                    test_method_name = 'test_{:04}_{:03}'.format(index, times_index)
                    test_method = _add_test(test_runner, test_dict)
                    setattr(TestSequense, test_method_name, test_method)

            loaded_testcase = self.test_loader.loadTestsFromTestCase(TestSequense)
            setattr(loaded_testcase, "config", config)
            setattr(loaded_testcase, "teststeps", tests)
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
            testcase_name = testcase.config.get("name")
            logger.log_info("开始运行测试用例: {}".format(testcase_name))

            result = self.unittest_runner.run(testcase)
            tests_results.append((testcase, result))

        return tests_results

    def _aggregate(self, tests_results, project_name):
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
            "platform": report.get_platform(),
            "details": []
        }

        for tests_result in tests_results:
            testcase, result = tests_result
            testcase_summary = report.get_summary(result)

            if testcase_summary["success"]:
                summary["stat"]["testcases"]["success"] += 1
            else:
                summary["stat"]["testcases"]["fail"] += 1

            summary["success"] &= testcase_summary["success"]
            testcase_summary["name"] = testcase.config.get("name")
            testcase_summary["in_out"] = utils.get_testcase_io(testcase)

            report.aggregate_stat(summary["stat"]["teststeps"], testcase_summary["stat"])
            report.aggregate_stat(summary["time"], testcase_summary["time"])

            summary["details"].append(testcase_summary)

        return summary

    def run_tests(self, tests_mapping):
        """ 运行testcase / testsuite数据 """
        if self.save_tests:
            utils.dump_tests(tests_mapping, "loaded")

        # 解析测试数据
        self.exception_stage = "parse tests"
        parsed_tests_mapping = parser.parse_tests(tests_mapping)

        if self.save_tests:
            utils.dump_tests(parsed_tests_mapping, "parsed")

        # 将测试添加到测试套件
        self.exception_stage = "add tests to test suite"
        test_suite = self._add_tests(parsed_tests_mapping)

        # 运行测试套件
        self.exception_stage = "run test suite"
        results = self._run_suite(test_suite)

        # 总体结果
        self.exception_stage = "aggregate results"
        self._summary = self._aggregate(results, project_name=tests_mapping.get('project'))

        # 生成html报告
        self.exception_stage = "generate html report"
        report.stringify_summary(self._summary)

        if self.save_tests:
            utils.dump_summary(self._summary, tests_mapping["project_mapping"])

        # report_path = report.render_html_report(
        #     self._summary,
        #     self.report_template,
        #     self.report_dir
        # )
        #
        # return report_path

    def get_vars_out(self):
        """ get variables and output
        Returns:
            list: list of variables and output.
                if tests are parameterized, list items are corresponded to parameters.

                [
                    {
                        "in": {
                            "user1": "leo"
                        },
                        "out": {
                            "out1": "out_value_1"
                        }
                    },
                    {...}
                ]

            None: returns None if tests not started or finished or corrupted.

        """
        if not self._summary:
            return None

        return [
            summary["in_out"]
            for summary in self._summary["details"]
        ]

    def run_path(self, path, dot_env_path=None, mapping=None):
        """ 运行 测试用例/测试套件 文件, 或文件夹。

        Args:
            path (str): 测试用例/测试套件 文件, 文件路径。
            dot_env_path (str): specified .env file path.
            mapping (dict): 如果指定了映射，它将覆盖config块中的变量。

        Returns:
            instance: HttpRunner() instance

        """
        # load tests
        self.exception_stage = "load tests"
        tests_mapping = loader.load_tests(path, dot_env_path)
        tests_mapping["project_mapping"]["test_path"] = path

        if mapping:
            tests_mapping["project_mapping"]["variables"] = mapping

        return self.run_tests(tests_mapping)

    def run(self, path_or_tests, dot_env_path=None, mapping=None):
        """ 执行测试的入口，判断是执行测试的数据源是路径还是字典
        Args:
            path_or_tests:
                str: 测试用例/测试套件文件/文件路径
                dict: 有效的测试用例/测试套件数据
        """
        if validator.is_testcase_path(path_or_tests):
            return self.run_path(path_or_tests, dot_env_path, mapping)
        elif validator.is_testcases(path_or_tests):
            return self.run_tests(path_or_tests)
        else:
            raise exceptions.ParamsError("测试数据错误，需为路径或字典: {}".format(path_or_tests))

    @property
    def summary(self):
        """ 获取测试结果和数据 """
        return self._summary


def prepare_locust_tests(path):
    """ prepare locust testcases

    Args:
        path (str): testcase file path.

    Returns:
        dict: locust tests data

            {
                "functions": {},
                "tests": []
            }

    """
    tests_mapping = loader.load_tests(path)
    parsed_tests_mapping = parser.parse_tests(tests_mapping)

    functions = parsed_tests_mapping.get("project_mapping", {}).get("functions", {})

    tests = []

    for testcase in parsed_tests_mapping["testcases"]:
        testcase_weight = testcase.get("config", {}).pop("weight", 1)
        for _ in range(testcase_weight):
            tests.append(testcase)

    return {
        "functions": functions,
        "tests": tests
    }
