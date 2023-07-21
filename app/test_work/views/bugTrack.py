# -*- coding: utf-8 -*-
from flask import current_app as app

from app.baseView import LoginRequiredView
from app.test_work.blueprint import test_work
from app.test_work.forms.bugTrack import GetBugListForm, GetBugForm, DeleteBugForm, AddBugForm, ChangeBugForm, \
    ChangeBugStatusForm, ChangeBugReplayForm
from app.test_work.models.bugTrack import BugTrack


class GetBugTrackListView(LoginRequiredView):

    def post(self):
        """ 获取bug列表 """
        form = GetBugListForm()
        return app.restful.success("获取成功", data=BugTrack.make_pagination(form.data))


class GetIterationListView(LoginRequiredView):

    def post(self):
        """ 获取迭代列表 """
        # [('2022-03-11',), ('2022-03-25',)]
        query_list = BugTrack.query.with_entities(BugTrack.iteration).distinct().all()
        return app.restful.success("获取成功", data=[query_res[0] for query_res in query_list])


class ChangeBugStatusView(LoginRequiredView):

    def put(self):
        """ 修改bug状态 """
        form = ChangeBugStatusForm().do_validate()
        form.bug.update({"status": form.status.data})
        return app.restful.success("修改成功", data=form.bug.to_dict())


class ChangeBugReplayView(LoginRequiredView):

    def put(self):
        """ 修改bug是否复盘 """
        form = ChangeBugReplayForm().do_validate()
        form.bug.update({"replay": form.replay.data})
        return app.restful.success("修改成功", data=form.bug.to_dict())


class BugTrackView(LoginRequiredView):
    """ 测试bug管理 """

    def get(self):
        """ 获取bug """
        form = GetBugForm().do_validate()
        return app.restful.success("获取成功", data=form.bug.to_dict())

    def post(self):
        """ 新增bug """
        form = AddBugForm().do_validate()
        form.num.data = BugTrack.get_insert_num()
        BugTrack().create(form.data)
        return app.restful.success("新增成功")

    def put(self):
        """ 修改bug """
        form = ChangeBugForm().do_validate()
        form.bug.update(form.data)
        return app.restful.success("修改成功", data=form.bug.to_dict())

    def delete(self):
        """ 删除bug """
        form = DeleteBugForm().do_validate()
        form.bug.delete()
        return app.restful.success("删除成功")


test_work.add_url_rule("/bugTrack", view_func=BugTrackView.as_view("BugTrackView"))
test_work.add_url_rule("/bugTrack/list", view_func=GetBugTrackListView.as_view("GetBugTrackListView"))
test_work.add_url_rule("/bugTrack/status", view_func=ChangeBugStatusView.as_view("ChangeBugStatusView"))
test_work.add_url_rule("/bugTrack/replay", view_func=ChangeBugReplayView.as_view("ChangeBugReplayView"))
test_work.add_url_rule("/bugTrack/iteration", view_func=GetIterationListView.as_view("GetIterationListView"))
