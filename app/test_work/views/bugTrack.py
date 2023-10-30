# -*- coding: utf-8 -*-
from flask import current_app as app

from app.test_work.blueprint import test_work
from app.test_work.forms.bugTrack import GetBugListForm, GetBugForm, DeleteBugForm, AddBugForm, ChangeBugForm, \
    ChangeBugStatusForm, ChangeBugReplayForm
from app.test_work.models.bugTrack import BugTrack


@test_work.login_post("/bugTrack/list")
def test_work_get_bug_track_list():
    """ 获取bug列表 """
    form = GetBugListForm()
    return app.restful.success("获取成功", data=BugTrack.make_pagination(form.data))


@test_work.login_post("/bugTrack/iteration")
def test_work_get_bug_track_iteration():
    """ 获取迭代列表 """
    # [('2022-03-11',), ('2022-03-25',)]
    query_list = BugTrack.query.with_entities(BugTrack.iteration).distinct().all()
    return app.restful.success("获取成功", data=[query_res[0] for query_res in query_list])


@test_work.login_put("/bugTrack/status")
def test_work_change_bug_track_status():
    """ 修改bug状态 """
    form = ChangeBugStatusForm().do_validate()
    form.bug.update({"status": form.status.data})
    return app.restful.success("修改成功", data=form.bug.to_dict())


@test_work.login_put("/bugTrack/replay")
def test_work_change_bug_track_replay():
    """ 修改bug是否复盘 """
    form = ChangeBugReplayForm().do_validate()
    form.bug.update({"replay": form.replay.data})
    return app.restful.success("修改成功", data=form.bug.to_dict())


@test_work.login_get("/bugTrack")
def test_work_get_bug_track():
    """ 获取bug """
    form = GetBugForm().do_validate()
    return app.restful.success("获取成功", data=form.bug.to_dict())


@test_work.login_post("/bugTrack")
def test_work_add_bug_track():
    """ 新增bug """
    form = AddBugForm().do_validate()
    form.num.data = BugTrack.get_insert_num()
    BugTrack().create(form.data)
    return app.restful.success("新增成功")


@test_work.login_put("/bugTrack")
def test_work_change_bug_track():
    """ 修改bug """
    form = ChangeBugForm().do_validate()
    form.bug.update(form.data)
    return app.restful.success("修改成功", data=form.bug.to_dict())


@test_work.login_delete("/bugTrack")
def test_work_delete_bug_track():
    """ 删除bug """
    form = DeleteBugForm().do_validate()
    form.bug.delete()
    return app.restful.success("删除成功")
