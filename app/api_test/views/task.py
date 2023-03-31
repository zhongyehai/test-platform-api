# -*- coding: utf-8 -*-
from flask import current_app as app, request, g

from app.api_test.models.report import ApiReport as Report
from app.api_test.models.case import ApiCase as Case
from app.api_test.models.caseSet import ApiCaseSet as CaseSet
from app.baseView import LoginRequiredView, NotLoginView
from app.busines import TaskBusiness, RunCaseBusiness
from app.system.models.user import User
from utils.client.runApiTest import RunCase
from app.api_test.blueprint import api_test
from app.api_test.models.task import ApiTask as Task
from app.api_test.forms.task import RunTaskForm, AddTaskForm, EditTaskForm, HasTaskIdForm, DeleteTaskIdForm, \
    GetTaskListForm


class ApiRunTaskView(NotLoginView):
    def post(self):
        """ 运行定时任务 """
        form = RunTaskForm().do_validate()
        case_id = CaseSet.get_case_id(
                Case, form.task.project_id, form.task.loads(form.task.set_ids), form.task.loads(form.task.case_ids)
            )
        run_id = Report.get_run_id()
        env_list = form.env_list.data or form.loads(form.task.env_list)
        for env_code in env_list:
            RunCaseBusiness.run(
                run_id=run_id,
                env_code=env_code,
                trigger_type=form.trigger_type.data,
                is_async=form.is_async.data,
                project_id=form.task.project_id,
                report_name=form.task.name,
                task_type="task",
                report_model=Report,
                case_id=case_id,
                run_type="api",
                run_func=RunCase,
                task=form.task.to_dict(),
                create_user=g.user_id or User.get_first(account="common").id
            )
        return app.restful.success(msg="触发执行成功，请等待执行完毕", data={"run_id": run_id})


class ApiTaskListView(LoginRequiredView):
    def get(self):
        """ 任务列表 """
        form = GetTaskListForm().do_validate()
        return app.restful.success(data=Task.make_pagination(form))


class ApiChangeTaskSortView(LoginRequiredView):
    def put(self):
        """ 更新定时任务的排序 """
        Task.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class ApiCopyTaskView(LoginRequiredView):
    def post(self):
        """ 复制定时任务 """
        form = HasTaskIdForm().do_validate()
        new_task = TaskBusiness.copy(form, Task)
        return app.restful.success(msg="复制成功", data=new_task.to_dict())


class ApiTaskView(LoginRequiredView):

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
        form.num.data = Task.get_insert_num(project_id=form.project_id.data)
        form.task.update(form.data)
        return app.restful.success(f"任务【{form.name.data}】修改成功", form.task.to_dict())

    def delete(self):
        """ 删除定时任务 """
        form = DeleteTaskIdForm().do_validate()
        form.task.delete()
        return app.restful.success(f"任务【{form.task.name}】删除成功")


class ApiTaskStatusView(LoginRequiredView):
    """ 任务状态修改 """

    def post(self):
        """ 启用定时任务 """
        form = HasTaskIdForm().do_validate()
        res = TaskBusiness.enable(form, "api")
        if res["status"] == 1:
            return app.restful.success(f"任务【{form.task.name}】启用成功", data=res["data"])
        else:
            return app.restful.fail(f"任务【{form.task.name}】启用失败", data=res["data"])

    def delete(self):
        """ 禁用定时任务 """
        form = HasTaskIdForm().do_validate()
        res = TaskBusiness.disable(form, "api")
        if res["status"] == 1:
            return app.restful.success(f"任务【{form.task.name}】禁用成功", data=res["data"])
        else:
            return app.restful.fail(f"任务【{form.task.name}】禁用失败", data=res["data"])


api_test.add_url_rule("/task", view_func=ApiTaskView.as_view("ApiTaskView"))
api_test.add_url_rule("/task/run", view_func=ApiRunTaskView.as_view("ApiRunTaskView"))
api_test.add_url_rule("/task/copy", view_func=ApiCopyTaskView.as_view("ApiCopyTaskView"))
api_test.add_url_rule("/task/list", view_func=ApiTaskListView.as_view("ApiTaskListView"))
api_test.add_url_rule("/task/status", view_func=ApiTaskStatusView.as_view("ApiTaskStatusView"))
api_test.add_url_rule("/task/sort", view_func=ApiChangeTaskSortView.as_view("ApiChangeTaskSortView"))
