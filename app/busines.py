#!/usr/bin/env python
from threading import Thread

import requests
from flask import g, request


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
    def put(cls, form, env_model):
        form.env_data.update(form.data)

        # 更新环境的时候，把环境的头部信息、变量的key一并同步到其他环境
        env_list = [
            env.env for env in env_model.get_all(project_id=form.project_id.data) if env.env != form.env_data.env
        ]
        env_model.synchronization(form.env_data, env_list, ["variables", 'headers'])


class ModuleBusiness:
    """ 模块管理业务 """

    @classmethod
    def post(cls, form, model):
        form.num.data = model.get_insert_num(project_id=form.project_id.data)
        new_model = model().create(form.data)
        setattr(new_model, 'children', [])
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
        old_case['create_user'] = old_case['update_user'] = g.user_id
        old_case['name'] = old_case['name'] + '_copy'
        old_case['num'] = case_model.get_insert_num(set_id=old_case['set_id'])
        new_case = case_model().create(old_case)

        # 复制步骤
        old_step_list = step_model.query.filter_by(case_id=form.case.id).order_by(step_model.num.asc()).all()
        step_list = []
        for index, old_step in enumerate(old_step_list):
            step = old_step.to_dict()
            step['num'] = index
            step['case_id'] = new_case.id
            new_step = step_model().create(step)
            if step_type == 'api':
                new_step.add_api_quote_count()
            step_list.append(new_step.to_dict())
        return {'case': new_case.to_dict(), 'steps': step_list}

    @classmethod
    def copy_step_to_current_case(cls, form, step_model):
        """ 复制指定用例的步骤到当前用例下 """
        from_case, to_case = form.source_case, form.to_case
        step_list, num_start = [], step_model.get_max_num(case_id=to_case.id)
        for index, step in enumerate(
                step_model.query.filter_by(case_id=from_case.id).order_by(step_model.num.asc()).all()):
            step_dict = step.to_dict()
            step_dict['case_id'], step_dict['num'] = to_case.id, num_start + index + 1
            step_list.append(step_model().create(step_dict).to_dict())
        return step_list


class StepBusiness:
    """ 步骤业务 """

    @classmethod
    def post(cls, form, step_model, case_model, step_type=None):
        form.num.data = step_model.get_insert_num(case_id=form.case_id.data)
        step = step_model().create(form.data)
        if step_type == 'api':
            step.add_api_quote_count()
        case_model.merge_variables(step.quote_case, step.case_id)
        return step

    @classmethod
    def copy(cls, step_id, step_model, step_type=None):
        old = step_model.get_first(step_id).to_dict()
        old['name'] = f"{old['name']}_copy"
        old['num'] = step_model.get_insert_num(case_id=old['case_id'])
        step = step_model().create(old)
        if step_type == 'api':
            step.add_api_quote_count()
        return step


class TaskBusiness:
    """ 任务业务 """

    # @classmethod
    # def post(cls, form, step_model, case_model, step_type=None):
    #     form.num.data = step_model.get_insert_num(case_id=form.case_id.data)
    #     step = step_model().create(form.data)
    #     if step_type == 'api':
    #         step.add_api_quote_count()
    #     case_model.merge_variables(step.quote_case, step.case_id)
    #     return step

    @classmethod
    def copy(cls, form, task_model):
        old_task = form.task.to_dict()
        old_task["name"], old_task["status"] = old_task["name"] + '_copy', 0
        old_task["num"] = task_model.get_insert_num(project_id=old_task["project_id"])
        new_task = task_model().create(old_task)
        return new_task

    @classmethod
    def enable(cls, form, task_type):
        """ 启用任务 """
        try:
            res = requests.post(
                url='http://localhost:8025/api/job/status',
                headers=request.headers,
                json={
                    'userId': g.user_id,
                    'task': form.task.to_dict(),
                    'type': task_type
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
                url='http://localhost:8025/api/job/status',
                headers=request.headers,
                json={
                    'taskId': form.task.id,
                    'type': task_type
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
    def run(cls,
            form,
            project_id,
            report_name,
            run_type,
            report_model,
            case_id,
            run_func,
            performer=None,
            create_user=None
            ):
        """ 运行用例/任务 """
        env = form.env.data.lower() if form.env.data else form.task.env
        trigger_type = form.trigger_type.data if hasattr(form, "trigger_type") else None
        report = report_model.get_new_report(
            name=report_name,
            run_type=run_type,
            performer=performer,
            create_user=create_user,
            project_id=project_id,
            env=env,
            trigger_type=trigger_type
        )
        # 新起线程运行任务
        Thread(
            target=run_func(
                project_id=project_id,
                report_id=report.id,
                run_name=report.name,
                case_id=case_id,
                is_async=form.is_async.data,
                env=env,
                trigger_type=trigger_type
            ).run_case
        ).start()
        return report.id
