# -*- coding: utf-8 -*-
from threading import Thread

import requests
from flask import g, request

from app.app_ui_test.models.project import AppUiProject
from app.config.models.runEnv import RunEnv


class ProjectBusiness:
    """ 项目管理业务 """

    @classmethod
    def post(cls, form, project_model, env_model, case_set_model):
        form.num.data = project_model.get_insert_num()
        project = project_model().create(form.data)
        env_model.create_env(project.id)  # 新增服务的时候，一并把环境设置齐全
        case_set_model.create_case_set_by_project(project.id)  # 新增服务的时候，一并把用例集设置齐全
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
    def post(cls, form, model):
        form.num.data = model.get_insert_num(module_id=form.module_id.data)
        new_element = model().create(form.data)
        form.update_page_addr()
        return new_element


class CaseBusiness:
    """ 用例业务 """

    @classmethod
    def copy(cls, form, case_model, step_model, step_type=None):
        # 复制用例
        old_case = form.case.to_dict()
        old_case["create_user"] = old_case["update_user"] = g.user_id
        old_case["name"] = old_case["name"] + "_copy"
        old_case["num"] = case_model.get_insert_num(set_id=old_case["set_id"])
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
    def copy_step_to_current_case(cls, form, step_model):
        """ 复制指定用例的步骤到当前用例下 """
        from_case, to_case = form.source_case, form.to_case
        step_list, num_start = [], step_model.get_max_num(case_id=to_case.id)
        for index, step in enumerate(
                step_model.query.filter_by(case_id=from_case.id).order_by(step_model.num.asc()).all()):
            step_dict = step.to_dict()
            step_dict["case_id"], step_dict["num"] = to_case.id, num_start + index + 1
            step_list.append(step_model().create(step_dict).to_dict())
            step.add_quote_count()
        return step_list

    @classmethod
    def pull_step_to_current_case(cls, form, step_model):
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
    def put(cls, form, project_model, case_set_model, case_model, step_model):
        """ 更新步骤 """
        form.case.update(form.data)
        cls.change_quote_case_name(form.id.data, project_model, case_set_model, case_model, step_model)

    @classmethod
    def get_quote_case_belong_to(cls, case_id, project_model, case_set_model, case_model):
        """ 获取用例的归属 """
        case = case_model.get_first(id=case_id)
        case_set_list = case_set_model.get_case_set_by_case(case.set_id)
        project = project_model.get_first(id=case_set_list[0].project_id)
        case_set_name = '/'.join([case_set.name for case_set in case_set_list])
        return f'{project.name}/{case_set_name}/{case.name}'

    @classmethod
    def change_quote_case_name(cls, case_id, project_model, case_set_model, case_model, step_model):
        """ 修改用例时，修改引用此用例的步骤的名字 """
        new_name = cls.get_quote_case_belong_to(case_id, project_model, case_set_model, case_model)
        for step in step_model.get_all(quote_case=case_id):
            step.update({"name": f'引用【{new_name}】'})


class StepBusiness:
    """ 步骤业务 """

    @classmethod
    def post(cls, form, step_model, case_model, step_type=None):
        form.num.data = step_model.get_insert_num(case_id=form.case_id.data)
        step = step_model().create(form.data)
        if step_type == "api":
            step.add_quote_count()
        case_model.merge_variables(step.quote_case, step.case_id)
        return step

    @classmethod
    def copy(cls, step_id, case_id, step_model, step_type=None):
        """ 复制步骤，如果没有指定用例id，则默认复制到当前用例下 """
        old = step_model.get_first(id=step_id).to_dict()
        old["name"] = f'{old["name"]}_copy'
        old["num"] = step_model.get_insert_num(case_id=case_id if case_id else old["case_id"])
        if case_id:
            old["case_id"] = case_id
        step = step_model().create(old)
        if step_type == "api":
            step.add_quote_count()
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
            env_code,
            is_async,
            project_id,
            report_name,
            task_type,
            report_model,
            case_id,
            run_type,
            run_func,
            browser=None,
            report_id=None,
            trigger_type="page",
            task={},
            appium_config={},
            extend_data={},
            create_user=None
    ):
        env = RunEnv.get_data_byid_or_code(env_code)
        """ 运行用例/任务 """
        report = report_id or report_model.get_new_report(
            name=report_name,
            run_type=task_type,
            create_user=create_user,
            project_id=project_id,
            env=env.code,
            trigger_type=trigger_type
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
                browser=browser,
                task=task,
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
            "platformName": phone["os"],
            "platformVersion": phone["os_version"],
            "deviceName": phone["name"],
            "appPackage": project["app_package"],
            "appActivity": project["app_activity"],
            "unicodeKeyboard": True,  # 使用Unicode编码方式发送字符串
            "resetKeyboard": True,  # 是否调用appium键盘
            "noReset": form.no_reset.data,  # 控制APP记录的信息是否不重置
            # "app": "",  # 安装路径
            # "browserName": "",  # 直接测web用, Chrome
            # "autoWebview": "",  # 开机进入webview模式
        }
