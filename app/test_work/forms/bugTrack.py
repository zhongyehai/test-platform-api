# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

from app.baseForm import BaseForm
from ..models.bugTrack import BugTrack


class GetBugListForm(BaseForm):
    """ 获取bug列表 """
    page_num = IntegerField()
    page_size = IntegerField()
    business_list = StringField()
    name = StringField()
    detail = StringField()
    status = StringField()
    replay = StringField()
    conclusion = StringField()
    iteration = StringField()


class GetBugForm(BaseForm):
    """ bug详情 """
    id = IntegerField(validators=[DataRequired("id必传")])

    def validate_id(self, field):
        bug = self.validate_data_is_exist(f"id为 {field.data} 的bug不存在", BugTrack, id=field.data)
        setattr(self, "bug", bug)


class DeleteBugForm(GetBugForm):
    """ 删除bug """


class AddBugForm(BaseForm):
    """ 添加bug """
    business_id = IntegerField(validators=[DataRequired("请选择业务线")])
    name = StringField(validators=[DataRequired("请输入bug名字")])
    detail = StringField(validators=[DataRequired("请输入bug详情")])
    iteration = StringField(validators=[DataRequired("请输入或选择迭代")])
    bug_from = StringField()
    trigger_time = StringField()
    manager = StringField()
    reason = StringField()
    solution = StringField()
    num = IntegerField()


class ChangeBugForm(GetBugForm, AddBugForm):
    """ 修改bug """

    # business_id = IntegerField(validators=[DataRequired("请选择业务线")])
    # name = StringField(validators=[DataRequired("请输入bug名字")])
    # detail = StringField(validators=[DataRequired("请输入bug详情")])
    # iteration = StringField(validators=[DataRequired("请输入迭代")])
    # replay = IntegerField()
    # conclusion = StringField()
    # bug_from = StringField()
    # trigger_time = StringField()
    # manager = StringField()
    # reason = StringField()
    # solution = StringField()

    def validate_replay(self, field):
        """ 已复盘，则必须有复盘结论 """
        if field.data:
            self.validate_data_is_true("请输入复盘结论", self.conclusion.data)


class ChangeBugStatusForm(GetBugForm):
    """ 修改bug状态 """
    status = StringField(validators=[DataRequired("bug状态必传")])


class ChangeBugReplayForm(GetBugForm):
    """ 修改bug是否复盘 """
    replay = StringField(validators=[DataRequired("复盘状态必传")])
