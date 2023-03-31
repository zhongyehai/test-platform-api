# -*- coding: utf-8 -*-
from flask import request, g, current_app as app

from app.baseView import LoginRequiredView, NotLoginView
from app.busines import TaskBusiness, RunCaseBusiness
from app.system.models.user import User
from app.app_ui_test.models.report import AppUiReport as Report
from app.app_ui_test.models.case import AppUiCase as Case
from app.app_ui_test.models.caseSet import AppUiCaseSet as CaseSet
from utils.client.runUiTest import RunCase
from app.app_ui_test.blueprint import app_ui_test
from app.app_ui_test.models.task import AppUiTask as Task
from app.app_ui_test.forms.task import RunTaskForm, AddTaskForm, EditTaskForm, HasTaskIdForm, DeleteTaskIdForm, \
    GetTaskListForm, DisableTaskIdForm


class AppUiRunTaskView(NotLoginView):

    def post(self):
        """ 单次运行定时任务 """
        form = RunTaskForm().do_validate()
        case_id = CaseSet.get_case_id(
                Case, form.task.project_id, form.task.loads(form.task.set_ids), form.task.loads(form.task.case_ids)
            )
        appium_config = RunCaseBusiness.get_appium_config(form.task.project_id, form)
        run_id = Report.get_run_id()
        RunCaseBusiness.run(
            run_id=run_id,
            trigger_type=form.trigger_type.data,
            is_async=form.is_async.data,
            project_id=form.task.project_id,
            report_name=form.task.name,
            task_type="task",
            report_model=Report,
            case_id=case_id,
            run_type="app",
            run_func=RunCase,
            task=form.task.to_dict(),
            create_user=g.user_id or User.get_first(account="common").id,
            appium_config=appium_config
        )
        return app.restful.success(msg="触发执行成功，请等待执行完毕", data={"run_id": run_id})


class AppUiGetTaskListView(LoginRequiredView):

    def get(self):
        """ 任务列表 """
        form = GetTaskListForm().do_validate()
        return app.restful.success(data=Task.make_pagination(form))


class AppUiChangeTaskSortView(LoginRequiredView):

    def put(self):
        """ 更新定时任务的排序 """
        Task.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class AppUiTaskCopyView(LoginRequiredView):

    def post(self):
        """ 复制任务 """
        form = HasTaskIdForm().do_validate()
        new_task = TaskBusiness.copy(form, Task)
        return app.restful.success(msg="复制成功", data=new_task.to_dict())


class AppUiTaskView(LoginRequiredView):

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


class AppUiTaskStatusView(LoginRequiredView):

    def post(self):
        """ 启用任务 """
        form = HasTaskIdForm().do_validate()
        res = TaskBusiness.enable(form, "appUi")
        if res["status"] == 1:
            return app.restful.success(f"任务【{form.task.name}】启用成功", data=res["data"])
        else:
            return app.restful.fail(f"任务【{form.task.name}】启用失败", data=res["data"])

    def delete(self):
        """ 禁用任务 """
        form = DisableTaskIdForm().do_validate()
        res = TaskBusiness.disable(form, "appUi")
        if res["status"] == 1:
            return app.restful.success(f"任务【{form.task.name}】禁用成功", data=res["data"])
        else:
            return app.restful.fail(f"任务【{form.task.name}】禁用失败", data=res["data"])


app_ui_test.add_url_rule("/task", view_func=AppUiTaskView.as_view("AppUiTaskView"))
app_ui_test.add_url_rule("/task/run", view_func=AppUiRunTaskView.as_view("AppUiRunTaskView"))
app_ui_test.add_url_rule("/task/copy", view_func=AppUiTaskCopyView.as_view("AppUiTaskCopyView"))
app_ui_test.add_url_rule("/task/list", view_func=AppUiGetTaskListView.as_view("AppUiGetTaskListView"))
app_ui_test.add_url_rule("/task/status", view_func=AppUiTaskStatusView.as_view("AppUiTaskStatusView"))
app_ui_test.add_url_rule("/task/sort", view_func=AppUiChangeTaskSortView.as_view("AppUiChangeTaskSortView"))
