import time
import unittest

from . import (exceptions, logger, parser, report, runner, utils, validator)


class UiTestRunner(object):

    def __init__(self,
                 failfast=False,
                 save_tests=False,
                 report_template=None,
                 report_dir=None,
                 log_level="INFO",
                 log_file=None):
        """ 初始化 HttpRunner.
        Args:
            failfast (bool): 设置为 True 时，测试在首次遇到错误或失败时会停止运行；默认值为 False
            report_template (str): 测试报告模板文件路径，模板应为Jinja2格式。
            report_dir (str): html报告保存目录。
            log_level (str): 设置日志级别，默认为 "INFO"
            log_file (str): 设置日志文件路径，指定后将同时输出日志文件；默认不输出日志文件
        """
        self.exception_stage = "初始化 UiTestRunner"
        kwargs = {
            "failfast": failfast,
            "resultclass": report.HtmlTestResult
        }
        self.unittest_runner = unittest.TextTestRunner(**kwargs)
        self.test_loader = unittest.TestLoader()
        self.report_template = report_template
        self.report_dir = report_dir
        self.save_tests = save_tests
        self._summary = None
        if log_file:
            logger.setup_logger(log_level, log_file)

    def _add_tests(self, tests_mapping: dict):
        """ 初始化 Runner() ，并把测试数据添加到测试集
        Args:
            tests_mapping (dict): 项目信息和用例列表
        Returns:
            unittest.TestSuite()
        """

        def _add_test(test_runner, test_step: dict):
            """ 将测试步骤添加到测试用例。"""

            def test(self):
                try:
                    test_runner.run_test(test_step)
                except exceptions.MyBaseFailure as ex:
                    self.fail(str(ex))
                finally:
                    self.meta_datas = test_runner.meta_datas

            # 测试步骤方法的名字
            test.__doc__ = test_step["config"].get("name") if "config" in test_step else test_step.get("name")

            return test

        test_suite = unittest.TestSuite()
        functions = tests_mapping.get("project_mapping", {}).get("functions", {})

        for testcase in tests_mapping["testcases"]:
            config = testcase.get("config", {})
            test_runner = runner.Runner(config, functions)

            test_case_container = type('test_case_container', (unittest.TestCase,), {})

            steps = testcase.get("teststeps", [])
            for index, step in enumerate(steps):
                for times_index in range(int(step.get("times", 1))):
                    # 构建测试函数，反射到测试类
                    # 一条用例测试步骤不应该超过9999个，一个步骤运行次数不应该超过999次
                    test_method_name = 'test_{:04}_{:03}'.format(index, times_index)
                    test_method = _add_test(test_runner, step)
                    setattr(test_case_container, test_method_name, test_method)

            loaded_testcase = self.test_loader.loadTestsFromTestCase(test_case_container)
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

    def _aggregate(self, tests_results: list, project_name: str):
        """ 汇总测试数据和结果 """
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

    def run_tests(self, tests_mapping: dict):
        """ 运行testcase / testsuite数据 """

        self.exception_stage = "解析测试数据"
        parsed_tests_mapping = parser.parse_tests(tests_mapping)

        self.exception_stage = "添加测试数据到测试集"
        test_suite = self._add_tests(parsed_tests_mapping)

        self.exception_stage = "运行测试套件"
        results = self._run_suite(test_suite)

        self.exception_stage = "汇总结果"
        self._summary = self._aggregate(results, project_name=tests_mapping.get('project'))

        self.exception_stage = "测试报告数据转字符串"
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
        return [summary["in_out"] for summary in self._summary["details"]] if self._summary else None

    def run(self, tests: dict):
        """ 执行测试的入口，判断是执行测试的数据源是路径还是字典
        Args:
            tests: 有效的测试用例/测试套件数据
        """
        if validator.is_testcases(tests):
            return self.run_tests(tests)
        else:
            raise exceptions.ParamsError("测试数据错误，需为字典: {}".format(tests))

    @property
    def summary(self):
        """ 获取测试结果和数据 """
        return self._summary
