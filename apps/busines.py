# -*- coding: utf-8 -*-
from threading import Thread

from flask import current_app

from .app_test.model_factory import AppUiProject
from .config.model_factory import RunEnv, Config


class RunCaseBusiness:
    """ 运行用例 """

    @classmethod
    def run(
            cls, is_async, task_type, project_id, batch_id, report_model, report_name, case_id_list, runner, env_code,
            run_type=None, temp_variables={}, trigger_id=None, browser=None, trigger_type="page", task_dict={},
            appium_config={}, extend_data={}
    ):
        """ 运行用例/任务 """

        env = RunEnv.get_data_by_id_or_code(env_code)
        summary = report_model.get_summary_template()
        summary["env"]["code"], summary["env"]["name"] = env.code, env.name

        report = report_model.get_new_report(
            project_id=project_id, batch_id=batch_id, trigger_id=trigger_id or case_id_list, name=report_name,
            run_type=task_type, env=env.code, trigger_type=trigger_type, temp_variables=temp_variables, summary=summary
        )
        # 新起线程运行任务
        Thread(
            target=runner(
                report_id=report.id, case_id_list=case_id_list, is_async=is_async, env_code=env.code, env_name=env.name,
                browser=browser, task_dict=task_dict, temp_variables=temp_variables, run_type=run_type,
                extend=extend_data, appium_config=appium_config, current_app=current_app
            ).parse_and_run
        ).start()
        return report.id

    @classmethod
    def get_appium_config(cls, project_id, form):
        """ 获取appium配置 """
        project = AppUiProject.get_first(id=project_id).to_dict()  # app配置
        server = form.server.to_dict()  # appium服务器配置
        phone = form.phone.to_dict()  # 运行手机配置
        appium_new_command_timeout = Config.get_appium_new_command_timeout() or 120
        appium_config = {
            "host": server["ip"],
            "port": server["port"],
            "newCommandTimeout": int(appium_new_command_timeout),  # 两条appium命令间的最长时间间隔，若超过这个时间，appium会自动结束并退出app，单位为秒
            "noReset": form.no_reset,  # 控制APP记录的信息是否不重置
            # "unicodeKeyboard": True,  # 使用 appium-ime 输入法
            # "resetKeyboard": True,  # 表示在测试结束后切回系统输入法

            # 设备参数
            "platformName": phone["os"],
            "platformVersion": phone["os_version"],
            "deviceName": phone["device_id"],

            # 用于后续自动化测试中的参数
            "server_id": server["id"],  # 用于判断跳过条件
            "phone_id": phone["id"],  # 用于判断跳过条件
            # "device": phone  # 用于插入到公共变量
            "device": {
                "id": phone["id"],
                "name": phone["name"],
                "os": phone["os"],
                "os_version": phone["os_version"],
                "device_id": phone["device_id"],
                "extends": phone["screen"],
                "screen": phone["screen"]
            }  # 用于插入到公共变量
        }
        if phone["os"] == "Android":  # 安卓参数
            appium_config["automationName"] = "UIAutomator2"
            appium_config["appPackage"] = project["app_package"]
            appium_config["appActivity"] = project["app_activity"]
        else:  # IOS参数
            appium_config["automationName"] = "XCUITest"
            appium_config["udid"] = phone["device_id"]  # 设备唯一识别号(可以使用Itunes查看UDID, 点击左上角手机图标 - 点击序列号直到出现UDID为止)
            appium_config["xcodeOrgId"] = ""  # 开发者账号id，可在xcode的账号管理中查看
            appium_config["xcodeSigningId"] = "iPhone Developer"

        return appium_config
