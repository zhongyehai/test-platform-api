# -*- coding: utf-8 -*-
import json
import os
from threading import Thread

import requests
from flask import g, request

from app.api_test.models.project import ApiProject, ApiProjectEnv
from app.app_ui_test.models.project import AppUiProject, AppUiProjectEnv
from app.config.models.runEnv import RunEnv
from app.web_ui_test.models.project import WebUiProject, WebUiProjectEnv
from utils.makeData.makeXmind import get_xmind_first_sheet_data
from utils.util.fileUtil import TEMP_FILE_ADDRESS


class ProjectBusiness:
    """ 项目管理业务 """

    @classmethod
    def post(cls, form, project_model, env_model, suite_model):
        form.num.data = project_model.get_insert_num()
        project = project_model().create(form.data)
        env_model.create_env(project.id)  # 新增服务的时候，一并把环境设置齐全
        suite_model.create_suite_by_project(project.id)  # 新增服务的时候，一并把用例集设置齐全
        return project


class ProjectEnvBusiness:
    """ 项目环境管理业务 """

    @classmethod
    def put(cls, form, env_model, filed_list):
        form.env_data.update(form.data)

        # 更新环境的时候，把环境的头部信息、变量的key一并同步到其他环境
        env_list = [
            env.env_id for env in env_model.get_all(project_id=form.project_id.data) if
            env.env_id != form.env_data.env_id
        ]
        env_model.synchronization(form.env_data, env_list, filed_list)

    @classmethod
    def add_env(cls, env_id):
        """ 批量给服务/项目/app添加运行环境 """
        ApiProjectEnv.add_env(env_id, ApiProject)
        WebUiProjectEnv.add_env(env_id, WebUiProject)
        AppUiProjectEnv.add_env(env_id, AppUiProject)


class ModuleBusiness:
    """ 模块管理业务 """

    @classmethod
    def post(cls, form, model):
        form.num.data = model.get_insert_num(project_id=form.project_id.data)
        new_model = model().create(form.data)
        setattr(new_model, "children", [])
        return new_model


class ElementBusiness:
    """ 元素管理业务 """

    @classmethod
    def post(cls, form, model, is_update_addr=False):
        element_list = []
        for element in form.element_list.data:
            element["project_id"] = form.project_id.data
            element["module_id"] = form.module_id.data
            element["page_id"] = form.page_id.data
            element["num"] = model.get_insert_num(page_id=form.page_id.data)
            new_element = model().create(element)
            element_list.append(new_element)
        if is_update_addr:
            form.update_page_addr()
        return element_list


class CaseSuiteBusiness:
    """ 用例集管理业务 """

    @classmethod
    def upload_case_suite(cls, project_id, file_obj, suite_model, case_model):
        file_path = os.path.join(TEMP_FILE_ADDRESS, file_obj.filename)
        file_obj.save(file_path)

        # 读取文件
        xmind_data = get_xmind_first_sheet_data(file_path)
        return suite_model.upload(project_id, xmind_data, case_model)


class CaseBusiness:
    """ 用例业务 """

    @classmethod
    def copy(cls, form, case_model, step_model, step_type=None):
        # 复制用例
        old_case = form.case.to_dict()
        old_case["create_user"] = old_case["update_user"] = g.user_id
        old_case["name"] = old_case["name"] + "_copy"
        old_case["num"] = case_model.get_insert_num(suite_id=old_case["suite_id"])
        old_case["status"] = 0
        new_case = case_model().create(old_case)

        # 复制步骤
        old_step_list = step_model.query.filter_by(case_id=form.case.id).order_by(step_model.num.asc()).all()
        step_list = []
        for index, old_step in enumerate(old_step_list):
            step = old_step.to_dict()
            step["num"] = index
            step["case_id"] = new_case.id
            new_step = step_model().create(step)
            if step_type == "api":
                new_step.add_quote_count()
            step_list.append(new_step.to_dict())
        return {"case": new_case.to_dict(), "steps": step_list}

    @classmethod
    def copy_case_all_step_to_current_case(cls, form, step_model, case_model):
        """ 复制指定用例的步骤到当前用例下 """
        from_case, to_case = form.source_case, form.to_case
        step_list, num_start = [], step_model.get_max_num(case_id=to_case.id)
        for index, step in enumerate(
                step_model.query.filter_by(case_id=from_case.id).order_by(step_model.num.asc()).all()):
            step_dict = step.to_dict()
            step_dict["case_id"], step_dict["num"] = to_case.id, num_start + index + 1
            step_list.append(step_model().create(step_dict).to_dict())
            if "Api" in step_model.__name__:  # 如果是api的，则增加接口引用
                step.add_quote_count()
        case_model.merge_output(to_case.id, step_list)  # 合并出参
        return step_list

    @classmethod
    def copy_step_to_current_case(cls, form, step_model):
        """ 拉取指定用例的步骤到指定用例下 """
        current_step, from_index = form.current_step, 0
        case_id = form.caseId.data or current_step.case_id

        to_list = step_model.query.filter_by(case_id=case_id).order_by(step_model.num.asc()).all()
        from_list = step_model.query.filter_by(case_id=current_step.quote_case).order_by(step_model.num.asc()).all()

        # current_step 本身就在用例中，则以current_step为节点分割步骤，把current_step对应的步骤出入到当前位置
        if current_step.case_id == case_id:
            index = to_list.index(current_step) + 1
            step_list = [*to_list[0:index], *from_list, *to_list[index:]]
        else:  # current_step 不在用例中，直接合并
            step_list = [*to_list, *from_list]
        # 遍历步骤，如果步骤的 case_id 等于 case_id 则更新，否则插入
        for index, step in enumerate(step_list):

            step_dict = step.to_dict()
            step_dict["num"] = index

            if step.case_id == case_id:
                step.update(step_dict, is_save_num=True)
            else:
                step_dict["case_id"] = case_id
                step_model().create(step_dict)

            if step in from_list:
                step.add_quote_count()

    @classmethod
    def get_quote_case_from(cls, case_id, project_model, suite_model, case_model):
        """ 获取用例的归属 """
        case = case_model.get_first(id=case_id)
        suite_path_name = suite_model.get_from_path(case.suite_id)
        suite = suite_model.get_first(id=case.suite_id)
        project = project_model.get_first(id=suite.project_id)
        return f'{project.name}/{suite_path_name}/{case.name}'


class StepBusiness:
    """ 步骤业务 """

    @classmethod
    def post(cls, form, step_model, case_model, step_type=None):
        """ 新增步骤 """
        form.num.data = step_model.get_insert_num(case_id=form.case_id.data)
        step = step_model().create(form.data)
        if step_type == "api":
            step.add_quote_count()
        case_model.merge_variables(step.quote_case, step.case_id)
        case_model.merge_output(step.case_id, [int(step.quote_case) if step.quote_case else step])  # 合并出参
        return step

    @classmethod
    def copy(cls, step_id, case_id, step_model, case_model, step_type=None):
        """ 复制步骤，如果没有指定用例id，则默认复制到当前用例下 """
        old = step_model.get_first(id=step_id).to_dict()
        old["name"] = f'{old["name"]}_copy'
        old["num"] = step_model.get_insert_num(case_id=case_id if case_id else old["case_id"])
        if case_id:
            old["case_id"] = case_id
        step = step_model().create(old)
        if step_type == "api":
            step.add_quote_count()
        case_model.merge_output(step.case_id, [step])  # 合并出参
        return step


class TaskBusiness:
    """ 任务业务 """

    @classmethod
    def copy(cls, form, task_model):
        old_task = form.task.to_dict()
        old_task["name"], old_task["status"] = old_task["name"] + "_copy", 0
        old_task["num"] = task_model.get_insert_num(project_id=old_task["project_id"])
        new_task = task_model().create(old_task)
        return new_task

    @classmethod
    def enable(cls, form, task_type):
        """ 启用任务 """
        try:
            res = requests.post(
                url="http://localhost:8025/api/job/status",
                headers=request.headers,
                json={
                    "userId": g.user_id,
                    "task": form.task.to_dict(),
                    "type": task_type
                }
            ).json()
            if res.get("status") == 200:
                form.task.enable()
                return {"status": 1, "data": res}
            else:
                return {"status": 0, "data": res}
        except Exception as error:
            return {"status": 0, "data": error}

    @classmethod
    def disable(cls, form, task_type):
        """ 禁用任务 """
        try:
            res = requests.delete(
                url="http://localhost:8025/api/job/status",
                headers=request.headers,
                json={
                    "taskId": form.task.id,
                    "type": task_type
                }
            ).json()
            if res.get("status") == 200:
                form.task.disable()
                return {"status": 1, "data": res}
            else:
                return {"status": 0, "data": res}
        except Exception as error:
            return {"status": 0, "data": error}


class RunCaseBusiness:
    """ 运行用例 """

    @classmethod
    def run(
            cls,
            is_async,
            project_id,
            report_name,
            task_type,
            report_model,
            case_id,
            run_type,
            run_func,
            temp_variables=None,
            trigger_id=None,  # 保存触发源的id，方便触发重跑
            batch_id=None,
            env_code=None,
            browser=None,
            report_id=None,
            trigger_type="page",
            task={},
            appium_config={},
            extend_data={},
            create_user=None
    ):
        """ 运行用例/任务 """

        env = RunEnv.get_data_byid_or_code(env_code)
        summary = report_model.get_summary_template()
        summary["run_type"], summary["is_async"] = run_type, is_async
        summary["run_env"], summary["env_name"] = env.code, env.name

        report = report_id or report_model.get_new_report(
            name=report_name,
            run_type=task_type,
            create_user=create_user,
            project_id=project_id,
            env=env.code,
            trigger_type=trigger_type,
            temp_variables=temp_variables,
            batch_id=batch_id,
            run_id=trigger_id or case_id,
            summary=summary
        )
        # 新起线程运行任务
        Thread(
            target=run_func(
                project_id=project_id,
                report_id=report.id,
                run_name=report.name,
                case_id=case_id,
                is_async=is_async,
                env_code=env.code,
                env_name=env.name,
                browser=browser,
                task=task,
                temp_variables=temp_variables,
                trigger_type=trigger_type,
                run_type=run_type,
                extend=extend_data,
                appium_config=appium_config
            ).run_case
        ).start()
        return report.id

    @classmethod
    def get_appium_config(cls, project_id, form):
        """ 获取appium配置 """
        project = AppUiProject.get_first(id=project_id).to_dict()  # app配置
        server = form.server.to_dict()  # appium服务器配置
        phone = form.phone.to_dict()  # 运行手机配置

        return {
            "host": server["ip"],
            "port": server["port"],
            # "newCommandTimeout": 6000,  # 两条appium命令间的最长时间间隔，若超过这个时间，appium会自动结束并退出app，单位为秒
            "noReset": form.no_reset.data,  # 控制APP记录的信息是否不重置
            # "unicodeKeyboard": True,  # 使用 appium-ime 输入法
            # "resetKeyboard": True,  # 表示在测试结束后切回系统输入法

            # 安卓参数
            "platformName": phone["os"],
            # "deviceName": phone["device_id"],
            "appPackage": project["app_package"],
            "appActivity": project["app_activity"],
            # "platformVersion": phone["os_version"],

            # 用于后续自动化测试中的参数
            "server_id": server["id"],  # 用于判断跳过条件
            "phone_id": phone["id"],  # 用于判断跳过条件
            "device": phone,  # 用于插入到公共变量
            # "app": r"D:\app-debug.apk",  # 安装路径
            # "browserName": "",  # 直接测web用, Chrome
            # "autoWebview": "",  # 开机进入webview模式
        }
