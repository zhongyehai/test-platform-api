# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import manage
from ..forms.bug_track import GetBugListForm, GetBugForm, DeleteBugForm, AddBugForm, ChangeBugForm, \
    ChangeBugStatusForm, ChangeBugReplayForm
from ..model_factory import BugTrack


@manage.login_get("/bug-track/list")
def manage_get_bug_track_list():
    """ 获取bug列表 """
    form = GetBugListForm()
    get_filed = [BugTrack.id, BugTrack.status, BugTrack.replay, BugTrack.business_id, BugTrack.name, BugTrack.detail,
                 BugTrack.iteration]
    return app.restful.get_success(BugTrack.make_pagination(form, get_filed=get_filed))


@manage.login_get("/bug-track/iteration")
def manage_get_bug_track_iteration():
    """ 获取迭代列表 """
    # [('2022-03-11',), ('2022-03-25',)]
    query_list = BugTrack.query.with_entities(BugTrack.iteration).distinct().all()
    return app.restful.get_success([query_res[0] for query_res in query_list])


@manage.login_put("/bug-track/status")
def manage_change_bug_track_status():
    """ 修改bug状态 """
    form = ChangeBugStatusForm()
    form.bug.model_update({"status": form.status})
    return app.restful.change_success()


@manage.login_put("/bug-track/replay")
def manage_change_bug_track_replay():
    """ 修改bug是否复盘 """
    form = ChangeBugReplayForm()
    form.bug.model_update({"replay": form.replay})
    return app.restful.change_success()


@manage.login_get("/bug-track")
def manage_get_bug_track():
    """ 获取bug """
    form = GetBugForm()
    return app.restful.get_success(form.bug.to_dict())


@manage.login_post("/bug-track")
def manage_add_bug_track():
    """ 新增bug """
    form = AddBugForm()
    BugTrack.model_create(form.model_dump())
    return app.restful.add_success()


@manage.login_put("/bug-track")
def manage_change_bug_track():
    """ 修改bug """
    form = ChangeBugForm()
    form.bug.model_update(form.model_dump())
    return app.restful.change_success()


@manage.login_delete("/bug-track")
def manage_delete_bug_track():
    """ 删除bug """
    form = DeleteBugForm()
    form.bug.delete()
    return app.restful.delete_success()
