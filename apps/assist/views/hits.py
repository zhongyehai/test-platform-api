# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import assist
from ..model_factory import Hits
from ..forms.hits import GetHitListForm, GetHitForm, CreatHitForm, EditHitForm, DeleteHitForm


@assist.login_get("/hit/type-list")
def assist_get_hit_type_list():
    """ 自动化测试命中问题类型列表 """
    hit_type_list = Hits.query.with_entities(Hits.hit_type).distinct().all()
    return app.restful.get_success([{"key": hit_type[0], "value": hit_type[0]} for hit_type in hit_type_list])


@assist.login_get("/hit/list")
def assist_get_hit_list():
    """ 自动化测试命中问题列表 """
    form = GetHitListForm()
    get_filed = [Hits.id, Hits.date, Hits.project_id, Hits.test_type, Hits.env, Hits.hit_type, Hits.hit_detail,
                 Hits.report_id, Hits.record_from, Hits.create_user]
    return app.restful.get_success(Hits.make_pagination(form, get_filed=get_filed))


@assist.login_get("/hit")
def assist_get_hit():
    """ 获取自动化测试命中问题 """
    form = GetHitForm()
    return app.restful.get_success(form.hit.to_dict())


@assist.login_post("/hit")
def assist_add_hit():
    """ 新增自动化测试命中问题 """
    form = CreatHitForm()
    Hits.model_create(form.model_dump())
    return app.restful.add_success()


@assist.login_put("/hit")
def assist_change_hit():
    """ 修改自动化测试命中问题 """
    form = EditHitForm()
    form.hit.model_update(form.model_dump())
    return app.restful.change_success(form.hit.to_dict())


@assist.login_delete("/hit")
def assist_delete_hit():
    """ 删除自动化测试命中问题 """
    form = DeleteHitForm()
    Hits.query.filter(Hits.id.in_(form.id_list)).delete()
    return app.restful.delete_success()
