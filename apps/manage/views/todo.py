# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import manage
from ..forms.todo import GetTodoForm, DeleteTodoForm, AddTodoForm, ChangeTodoForm, ChangeStatusForm
from ..model_factory import Todo
from ...base_form import ChangeSortForm


@manage.login_get("/todo/list")
def manage_get_todo_list():
    query_list = Todo.db.session.query(
        Todo.id, Todo.title, Todo.status, Todo.create_user, Todo.create_time).order_by(Todo.num.asc()).all()
    title_list = ["id", "title", "status", "create_user", "create_time"]
    data_list = [dict(zip(title_list, data)) for data in query_list]
    return app.restful.get_success(data_list)


@manage.login_put("/todo/sort")
def manage_change_todo_sort():
    """ 更新排序 """
    form = ChangeSortForm()
    Todo.change_sort(**form.model_dump())
    return app.restful.change_success()


@manage.login_put("/todo/status")
def manage_change_todo_status():
    form = ChangeStatusForm()
    form.todo.model_update({"status": form.status})
    return app.restful.change_success()


@manage.login_get("/todo")
def manage_get_todo():
    form = GetTodoForm()
    return app.restful.get_success(form.todo.to_dict())


@manage.login_post("/todo")
def manage_add_todo():
    form = AddTodoForm()
    Todo.model_batch_create(form.data_list)
    return app.restful.add_success()


@manage.login_put("/todo")
def manage_change_todo():
    form = ChangeTodoForm()
    form.todo.model_update(form.model_dump())
    return app.restful.change_success()


@manage.login_delete("/todo")
def manage_delete_todo():
    form = DeleteTodoForm()
    form.todo.delete()
    return app.restful.delete_success()
