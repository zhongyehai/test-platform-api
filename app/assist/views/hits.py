# -*- coding: utf-8 -*-
from flask import current_app as app

from app.baseView import LoginRequiredView
from app.assist.blueprint import assist
from app.assist.models.hits import Hits
from app.assist.forms.hits import GetHitListForm, HasHitForm, CreatHitForm, EditHitForm


class GetHitTypeListView(LoginRequiredView):

    def get(self):
        """ 自动化测试命中问题类型列表 """
        hit_type_list = Hits.query.with_entities(Hits.hit_type).distinct().all()
        return app.restful.success(
            "获取成功",
            data=[{"key": hit_type[0], "value": hit_type[0]} for hit_type in hit_type_list]
        )


class GetHitsListView(LoginRequiredView):

    def get(self):
        """ 自动化测试命中问题列表 """
        form = GetHitListForm().do_validate()
        return app.restful.success("获取成功", data=Hits.make_pagination(form))


class HitsView(LoginRequiredView):

    def get(self):
        """ 获取自动化测试命中问题 """
        form = HasHitForm().do_validate()
        return app.restful.success(msg="获取成功", data=form.hit.to_dict())

    def post(self):
        """ 新增自动化测试命中问题 """
        form = CreatHitForm().do_validate()
        Hits().create(form.data)
        return app.restful.success("创建成功")

    def put(self):
        """ 修改自动化测试命中问题 """
        form = EditHitForm().do_validate()
        form.hit.update(form.data)
        return app.restful.success("修改成功", data=form.hit.to_dict())

    def delete(self):
        """ 删除自动化测试命中问题 """
        form = HasHitForm().do_validate()
        form.hit.delete()
        return app.restful.success("删除成功")


assist.add_url_rule("/hit", view_func=HitsView.as_view("HitsView"))
assist.add_url_rule("/hit/list", view_func=GetHitsListView.as_view("GetHitsListView"))
assist.add_url_rule("/hit/type/list", view_func=GetHitTypeListView.as_view("GetHitTypeListView"))