# -*- coding: utf-8 -*-
from flask import request, g, current_app as app

from app.baseView import LoginRequiredView, NotLoginView
from app.busines import TaskBusiness, RunCaseBusiness
from app.system.models.user import User
from app.web_ui_test.models.report import WebUiReport as Report
from app.web_ui_test.models.case import WebUiCase as Case
from app.web_ui_test.models.caseSuite import WebUiCaseSuite as CaseSuite
from utils.client.runUiTest import RunCase
from app.web_ui_test.blueprint import web_ui_test
from app.web_ui_test.models.task import WebUiTask as Task
from app.web_ui_test.forms.task import RunTaskForm, AddTaskForm, EditTaskForm, HasTaskIdForm, DeleteTaskIdForm, \
    GetTaskListForm, DisableTaskIdForm


class WebUiRunTaskView(NotLoginView):

    def post(self):
        """ 单次运行定时任务 """
        form = RunTaskForm().do_validate()
        case_id = CaseSuite.get_case_id(
                Case, form.task.project_id, form.task.loads(form.task.suite_ids), form.task.loads(form.task.case_ids)
            )
        batch_id = Report.get_batch_id()
        env_list = form.env_list.data or form.loads(form.task.env_list)
        for env_code in env_list:
            RunCaseBusiness.run(
                batch_id=batch_id,
                env_code=env_code,
                browser=form.browser.data if hasattr(form, 'browser') else form.task.browser,
                trigger_type=form.trigger_type.data,
                is_async=form.is_async.data,
                project_id=form.task.project_id,
                report_name=form.task.name,
                task_type="task",
                report_model=Report,
                trigger_id=form.id.data,
                case_id=case_id,
                run_type="webUi",
                run_func=RunCase,
                task=form.task.to_dict(),
                create_user=g.user_id or User.get_first(account="common").id
        )
        return app.restful.success(msg="触发执行成功，请等待执行完毕", data={"batch_id": batch_id})


class WebUiGetTaskListView(LoginRequiredView):

    def get(self):
        """ 任务列表 """
        form = GetTaskListForm().do_validate()
        return app.restful.success(data=Task.make_pagination(form))


class WebUiChangeTaskSortView(LoginRequiredView):

    def put(self):
        """ 更新定时任务的排序 """
        Task.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class WebUiTaskCopyView(LoginRequiredView):

    def post(self):
        """ 复制任务 """
        form = HasTaskIdForm().do_validate()
        new_task = TaskBusiness.copy(form, Task)
        return app.restful.success(msg="复制成功", data=new_task.to_dict())


class WebUiTaskView(LoginRequiredView):

    def get(self):
        """ 获取定时任务 """
        form = HasTaskIdForm().do_validate()
        return app.restful.success(data=form.task.to_dict())

    def post(self):
        """ 新增定时任务 """
        form = AddTaskForm().do_validate()
        form.num.data = Task.get_insert_num(project_id=form.project_id.data)
        new_task = Task().create(form.data)
        return app.restful.success(f"任务【{form.name.data}】新建成功", new_task.to_dict())

    def put(self):
        """ 修改定时任务 """
        form = EditTaskForm().do_validate()
        form.task.update(form.data)
        return app.restful.success(f"任务【{form.name.data}】修改成功", form.task.to_dict())

    def delete(self):
        """ 删除定时任务 """
        form = DeleteTaskIdForm().do_validate()
        form.task.delete()
        return app.restful.success(f"任务【{form.task.name}】删除成功")


class WebUiTaskStatusView(LoginRequiredView):

    def post(self):
        """ 启用任务 """
        form = HasTaskIdForm().do_validate()
        res = TaskBusiness.enable(form, "webUi")
        if res["status"] == 1:
            return app.restful.success(f"任务【{form.task.name}】启用成功", data=res["data"])
        else:
            return app.restful.fail(f"任务【{form.task.name}】启用失败", data=res["data"])

    def delete(self):
        """ 禁用任务 """
        form = DisableTaskIdForm().do_validate()
        res = TaskBusiness.disable(form, "webUi")
        if res["status"] == 1:
            return app.restful.success(f"任务【{form.task.name}】禁用成功", data=res["data"])
        else:
            return app.restful.fail(f"任务【{form.task.name}】禁用失败", data=res["data"])


web_ui_test.add_url_rule("/task", view_func=WebUiTaskView.as_view("WebUiTaskView"))
web_ui_test.add_url_rule("/task/run", view_func=WebUiRunTaskView.as_view("WebUiRunTaskView"))
web_ui_test.add_url_rule("/task/copy", view_func=WebUiTaskCopyView.as_view("WebUiTaskCopyView"))
web_ui_test.add_url_rule("/task/list", view_func=WebUiGetTaskListView.as_view("WebUiGetTaskListView"))
web_ui_test.add_url_rule("/task/status", view_func=WebUiTaskStatusView.as_view("WebUiTaskStatusView"))
web_ui_test.add_url_rule("/task/sort", view_func=WebUiChangeTaskSortView.as_view("WebUiChangeTaskSortView"))
