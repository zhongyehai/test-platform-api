from typing import Optional

from flask import g
from pydantic import Field, field_validator

from ...base_form import BaseForm, PaginationForm, required_str_field
from ..model_factory import BugTrack
from ...system.models.user import User


class GetBugListForm(PaginationForm):
    """ 获取bug列表 """
    business_list: Optional[str] = Field(None, title="业务线")
    name: Optional[str] = Field(None, title="bug名字关键字")
    detail: Optional[str] = Field(None, title="bug详情关键字")
    status: Optional[str] = Field([], title="bug状态")
    replay: Optional[str] = Field(None, title="bug是否复盘")
    conclusion: Optional[str] = Field(None, title="复盘结论")
    iteration: Optional[str] = Field([], title="迭代")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []

        if self.business_list:
            filter_list.append(BugTrack.business_id.in_(self.business_list.split(',')))
        else:
            if User.is_not_admin():  # 非管理员则校验业务线权限
                filter_list.append(BugTrack.business_id.in_(g.business_list))
        if self.name:
            filter_list.append(BugTrack.name.like(f'%{self.name}%'))
        if self.detail:
            filter_list.append(BugTrack.detail.like(f'%{self.detail}%'))
        if self.status:
            filter_list.append(BugTrack.status.in_(self.status.split(',')))
        if self.replay:
            filter_list.append(BugTrack.replay == self.replay)
        if self.conclusion:
            filter_list.append(BugTrack.conclusion.like(f'%{self.conclusion}%'))
        if self.iteration:
            filter_list.append(BugTrack.iteration.in_(self.iteration.split(',')))
        return filter_list


class GetBugForm(BaseForm):
    """ bug详情 """
    id: int = Field(..., title="bug数据id")

    @field_validator("id")
    def validate_id(cls, value):
        bug = cls.validate_data_is_exist("数据不存在", BugTrack, id=value)
        setattr(cls, "bug", bug)
        return value


class DeleteBugForm(GetBugForm):
    """ 删除bug """


class ChangeBugStatusForm(GetBugForm):
    """ 修改bug状态 """
    status: str = required_str_field(title="bug状态")


class ChangeBugReplayForm(GetBugForm):
    """ 修改bug是否复盘 """
    replay: int = Field(..., title="复盘状态")


class AddBugForm(BaseForm):
    """ 添加bug """
    business_id: int = Field(..., title="业务线")
    iteration: str = required_str_field(title="迭代")
    name: str = required_str_field(title="bug描述")
    detail: str = required_str_field(title="bug详情")
    bug_from: Optional[str] = required_str_field(title="缺陷来源")
    trigger_time: Optional[str] = required_str_field(title="发现时间")
    reason: Optional[str] = Field(title="原因")
    solution: Optional[str] = Field(title="解决方案")
    manager: int = Field(..., title="跟进人")
    replay: int = Field(..., title="是否复盘")
    conclusion: Optional[str] = Field(..., title="复盘结论")

    def depends_validate(self):
        if self.replay == 1:
            self.validate_is_true(self.conclusion, '已复盘，则复盘结论必填')


class ChangeBugForm(GetBugForm, AddBugForm):
    """ 修改bug """
