# -*- coding: utf-8 -*-
from flask import current_app as app

from app.assist.blueprint import assist
from app.assist.models.hits import Hits
from app.assist.forms.hits import GetHitListForm, HasHitForm, CreatHitForm, EditHitForm


@assist.login_get("/hit/type/list")
def assist_get_hit_type_list():
    """ 自动化测试命中问题类型列表 """
    hit_type_list = Hits.query.with_entities(Hits.hit_type).distinct().all()
    return app.restful.success(
        "获取成功",
        data=[{"key": hit_type[0], "value": hit_type[0]} for hit_type in hit_type_list]
    )


@assist.login_get("/hit/list")
def assist_get_hit_list():
    """ 自动化测试命中问题列表 """
    form = GetHitListForm().do_validate()
    return app.restful.success("获取成功", data=Hits.make_pagination(form))


@assist.login_get("/hit")
def assist_get_hit():
    """ 获取自动化测试命中问题 """
    form = HasHitForm().do_validate()
    return app.restful.success(msg="获取成功", data=form.hit.to_dict())


@assist.login_post("/hit")
def assist_add_hit():
    """ 新增自动化测试命中问题 """
    form = CreatHitForm().do_validate()
    Hits().create(form.data)
    return app.restful.success("创建成功")


@assist.login_put("/hit")
def assist_change_hit():
    """ 修改自动化测试命中问题 """
    form = EditHitForm().do_validate()
    form.hit.update(form.data)
    return app.restful.success("修改成功", data=form.hit.to_dict())


@assist.login_delete("/hit")
def assist_delete_hit():
    """ 删除自动化测试命中问题 """
    form = HasHitForm().do_validate()
    form.hit.delete()
    return app.restful.success("删除成功")
